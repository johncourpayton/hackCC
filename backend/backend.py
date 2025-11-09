from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_apscheduler import APScheduler
import requests
import os
import sys
import json
import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Add server directory to path so server modules can import each other
server_dir = os.path.join(os.path.dirname(__file__), '..', 'server')
sys.path.insert(0, server_dir)

# Import server modules (they use relative imports like "from canvas import ...")
from discord_reminder import AssignmentReminderBot
from reminder_service import check_and_send_reminders, create_test_assignment
from reminder_tracker import ReminderTracker
from canvas import get_assignments_next_week
from gemini import generate_text_with_gemini

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure APScheduler to auto-start
app.config['SCHEDULER_API_ENABLED'] = True

# Initialize APScheduler
scheduler = APScheduler()
scheduler.init_app(app)
# Start scheduler immediately - it will run background jobs
scheduler.start()

# Global variables
USER_SETTINGS = {}  # Store user settings (Canvas domain, API token, Discord ID)
# Get scheduled user ID from environment variable or set to None (can be set via API)
scheduled_user_id = os.getenv("DISCORD_USER_ID", None)  # User ID for scheduled reminders
# Initialize reminder tracker with path relative to server directory
tracker_file_path = os.path.join(server_dir, "reminders_sent.json")
tracker = ReminderTracker(tracker_file=tracker_file_path)  # Initialize reminder tracker

# --- CANVAS CONFIGURATION (can be overridden by user settings) ---
CANVAS_DOMAIN = os.getenv("CANVAS_DOMAIN", "coastdistrict.instructure.com")
API_TOKEN = os.getenv("CANVAS_API_KEY", "")
START_DATE = "2025-11-08"  # Set your desired start date (YYYY-MM-DD)
END_DATE = "2025-11-15"    # Set your desired end date (YYYY-MM-DD)
COURSE_ID = None
# ------------------------------------------------------------------


def get_user_courses(canvas_domain: str = None, api_token: str = None):
    """
    Fetch all active courses for the user from Canvas.
    """
    canvas_domain = canvas_domain or USER_SETTINGS.get("canvas_domain") or CANVAS_DOMAIN
    api_token = api_token or USER_SETTINGS.get("api_token") or API_TOKEN
    
    if not canvas_domain or not api_token:
        return []
    
    api_url = f"https://{canvas_domain}/api/v1/courses"
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {"enrollment_state": "active", "per_page": 100}

    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        courses = response.json()
        print(f"Found {len(courses)} active courses.")
        return courses
    except requests.exceptions.RequestException as err:
        print(f"Error fetching courses: {err}")
    return []


def fetch_canvas_assignments():
    """
    Fetch assignments from Canvas using the saved user settings.
    """
    if not USER_SETTINGS:
        print("User settings not set! Cannot fetch assignments.")
        return []

    canvas_domain = USER_SETTINGS.get("canvas_domain")
    api_token = USER_SETTINGS.get("api_token")
    if not canvas_domain or not api_token:
        print("Canvas domain or API token missing!")
        return []

    # Parse dates as date objects (not datetime) to compare dates only, ignoring time
    start_date_obj = datetime.strptime(START_DATE, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(END_DATE, "%Y-%m-%d").date()
    
    courses = get_user_courses(canvas_domain, api_token)

    all_assignments = []
    headers = {"Authorization": f"Bearer {api_token}"}

    for course in courses:
        course_id = course.get("id")
        course_name = course.get("name", f"Course {course_id}")
        if not course_id:
            continue

        api_url = f"https://{canvas_domain}/api/v1/courses/{course_id}/assignments"
        # Remove bucket filter - fetch all assignments and filter by date range ourselves
        # This ensures we get assignments in our specific date range regardless of Canvas's bucket logic
        # Increase per_page to get more assignments (Canvas allows up to 100 per page)
        params = {"per_page": 100}

        try:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            assignments = response.json()
            
            # Handle pagination using Canvas Link header
            # Canvas API uses Link headers for pagination: <url>; rel="next"
            while 'Link' in response.headers:
                link_header = response.headers['Link']
                # Parse Link header to find next page
                next_url = None
                for link in link_header.split(','):
                    if 'rel="next"' in link:
                        next_url = link.split(';')[0].strip('<> ')
                        break
                
                if next_url:
                    response = requests.get(next_url, headers=headers)
                    response.raise_for_status()
                    assignments.extend(response.json())
                else:
                    break

            for assignment in assignments:
                due_at = assignment.get("due_at")
                # Only include assignments with due dates in our date range
                # Assignments without due dates are excluded
                if due_at:
                    try:
                        # Parse due date and extract just the date part for comparison
                        due_dt = datetime.fromisoformat(due_at.rstrip("Z"))
                        # Convert to UTC if timezone-aware, then get date only
                        if due_dt.tzinfo:
                            due_dt_utc = due_dt.astimezone(timezone.utc)
                            due_date_only = due_dt_utc.date()
                        else:
                            due_date_only = due_dt.date()
                        
                        # Compare dates only (ignoring time)
                        if start_date_obj <= due_date_only <= end_date_obj:
                            assignment["course_name"] = course_name
                            all_assignments.append(assignment)
                            print(f"  - Found assignment: {assignment.get('name', 'Unknown')} (Due: {due_date_only})")
                    except ValueError as e:
                        print(f"Error parsing due date for assignment {assignment.get('name', 'Unknown')}: {e}")
                        continue
                else:
                    # Log assignments without due dates for debugging
                    print(f"  - Skipping assignment '{assignment.get('name', 'Unknown')}' (no due date)")
        except requests.exceptions.RequestException as err:
            print(f"Error fetching assignments for {course_name}: {err}")

    # Format assignments for frontend
    formatted_assignments = []
    for a in all_assignments:
        due_date_str = a.get("due_at")
        formatted_due_date = "No Due Date"
        if due_date_str:
            try:
                due_date_utc = datetime.fromisoformat(due_date_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                local_timezone = ZoneInfo("America/Los_Angeles")
                due_date_local = due_date_utc.astimezone(local_timezone)
                formatted_due_date = due_date_local.strftime("%A, %B %d at %I:%M %p")
            except Exception as e:
                print(f"Error formatting date for {a.get('name')}: {e}")

        formatted_assignments.append({
            "name": a.get("name", "No Title"),
            "due_date": formatted_due_date,
            "course_name": a.get("course_name", "Unknown Course"),
            "description": a.get("description", ""),
            "priority": "high" if "exam" in a.get("name", "").lower() or "test" in a.get("name", "").lower() else "medium"
        })

    print(f"Found {len(formatted_assignments)} assignments in date range {START_DATE} to {END_DATE}")
    return formatted_assignments


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_id_from_settings(override_user_id=None):
    """
    Get Discord user ID from settings, with optional override.
    Priority: override_user_id > USER_SETTINGS > scheduled_user_id
    
    Args:
        override_user_id: Optional user ID to override settings
    
    Returns:
        User ID string or None if not found
    """
    if override_user_id:
        return str(override_user_id)
    
    # Check USER_SETTINGS first (from /api/settings)
    if USER_SETTINGS.get("discord_id"):
        return str(USER_SETTINGS.get("discord_id"))
    
    # Fall back to scheduled_user_id
    if scheduled_user_id:
        return str(scheduled_user_id)
    
    return None


# ============================================================================
# SCHEDULER JOB - Runs every 60 seconds to check for reminders
# ============================================================================

@scheduler.task('interval', id='check_reminders', seconds=60, misfire_grace_time=900, max_instances=1)
def scheduled_reminder_check():
    """
    Scheduled job that runs every 60 seconds to check for assignments due soon
    and send Discord reminders.
    Uses Discord user ID from USER_SETTINGS or scheduled_user_id.
    This function is automatically called by Flask-APScheduler every 60 seconds.
    """
    # Get user ID from settings (USER_SETTINGS takes priority)
    user_id = get_user_id_from_settings()
    
    if not user_id:
        # No user ID set for scheduled reminders, skip check
        print("[SCHEDULER] No Discord user ID configured. Skipping reminder check.")
        return
    
    try:
        print(f"[SCHEDULER] [{datetime.now(timezone.utc).isoformat()}] Running scheduled reminder check for user {user_id}")
        check_and_send_reminders(user_id=user_id, include_test=False, debug=False)
    except Exception as e:
        print(f"[SCHEDULER ERROR] Error in scheduled reminder check: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# CANVAS API ENDPOINTS
# ============================================================================

@app.route("/api/settings", methods=["POST"])
def set_user_settings():
    """
    Save user settings (Canvas API key, domain, Discord ID).
    """
    global USER_SETTINGS
    user_info = request.json

    USER_SETTINGS = {
        "canvas_domain": user_info.get("canvasDomain"),
        "api_token": user_info.get("apiKey"),
        "discord_id": user_info.get("discordId")
    }

    print("Saved user settings:", USER_SETTINGS)
    return jsonify({"status": "success"})


@app.route("/api/assignments", methods=["GET"])
def get_assignments():
    """
    Return assignments for the current user settings.
    Also triggers a reminder check if a Discord user ID is configured.
    """
    assignments = fetch_canvas_assignments()
    
    # Also check for reminders if a user ID is available
    discord_user_id = get_user_id_from_settings()
    
    if discord_user_id:
        try:
            # Trigger reminder check in background (non-blocking)
            # This will check assignments and send reminders if needed
            print(f"[API] Triggering reminder check for user {discord_user_id} (from /api/assignments)")
            check_and_send_reminders(user_id=discord_user_id, include_test=False, debug=False)
        except Exception as e:
            # Don't fail the request if reminder check fails
            print(f"[API] Warning: Reminder check failed: {e}")
    
    return jsonify(assignments)


@app.route("/generate-study-plan", methods=["POST"])
def generate_study_plan():
    """
    Generate a study plan using Gemini API based on assignment data.
    """
    try:
        data = request.json
        assignments = data.get("assignments", [])
        
        if not assignments:
            return jsonify({
                "status": "error",
                "message": "No assignments provided"
            }), 400
        
        # Format assignments for the prompt
        assignments_text = "\n".join([
            f"- {a.get('name', 'Unnamed Assignment')} (Due: {a.get('due_date', 'No due date')}, Priority: {a.get('priority', 'none')}, Description: {a.get('description', 'No description')})"
            for a in assignments
        ])
        
        # Use the same date range as Canvas assignments (START_DATE to END_DATE)
        # Parse dates as naive dates (date-only, no time) to avoid timezone shifts
        start_date_only = datetime.strptime(START_DATE, "%Y-%m-%d").date()
        end_date_only = datetime.strptime(END_DATE, "%Y-%m-%d").date()
        
        # Generate all dates from START_DATE to END_DATE (inclusive)
        week_dates = []
        current_date = start_date_only
        
        while current_date <= end_date_only:
            # Create datetime at noon local time to avoid timezone edge cases
            current_datetime = datetime.combine(current_date, datetime.min.time())
            local_timezone = ZoneInfo("America/Los_Angeles")
            current_datetime_local = current_datetime.replace(tzinfo=local_timezone)
            
            week_dates.append({
                "day_name": current_datetime_local.strftime('%A'),
                "date": current_date.strftime('%Y-%m-%d'),
                "full_date": current_datetime_local.strftime('%A, %B %d, %Y')
            })
            current_date += timedelta(days=1)
        
        # Create example JSON structure with actual dates
        example_schedule = ",\n    ".join([
            f'{{\n      "day": "{d["full_date"]}",\n      "date": "{d["date"]}",\n      "assignments": []\n    }}'
            for d in week_dates
        ])
        
        # Create a prompt for Gemini - requesting structured JSON format for date range
        prompt = f"""Create a study schedule for the following assignments for the date range from {START_DATE} to {END_DATE} ({len(week_dates)} days: {week_dates[0]["full_date"]} through {week_dates[-1]["full_date"]}).
You MUST return a JSON object with ALL {len(week_dates)} days in this date range - no exceptions.

Return ONLY a JSON object with this exact structure - no additional text, explanations, or tips:

{{
  "schedule": [
    {example_schedule}
  ]
}}

For days with assignments, include them like this:
{{
  "day": "{week_dates[0]["full_date"]}",
  "date": "{week_dates[0]["date"]}",
  "assignments": [
    {{
      "name": "Assignment Name",
      "time": "2:00 PM - 4:00 PM",
      "duration": "2 hours",
      "priority": "high"
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- You MUST include ALL {len(week_dates)} days from {START_DATE} to {END_DATE} in this exact order:
{chr(10).join([f"- {d['day_name']}: {d['full_date']} ({d['date']})" for d in week_dates])}
- Distribute assignments across the date range based on due dates and priority
- High priority assignments should be scheduled earlier in the date range
- Assignments due sooner should be scheduled earlier
- Spread the workload evenly across the days when possible
- Include ALL {len(week_dates)} days even if some days have no assignments (use empty assignments array: [])
- Use realistic time blocks (1-4 hours per assignment)
- Only include the date and time blocks - NO study tips, techniques, or advice
- Format times in 12-hour format (e.g., "2:00 PM - 4:00 PM")
- Use dates in format "YYYY-MM-DD" exactly as shown above
- Use full day names with dates exactly as shown above

Assignments:
{assignments_text}

Return ONLY valid JSON with ALL {len(week_dates)} days in the exact order shown above - no markdown, no code blocks, no explanations."""
        
        # Generate study plan using Gemini
        study_plan_response = generate_text_with_gemini(prompt)
        
        # Parse JSON from Gemini response (it might include markdown code blocks)
        try:
            # Try to extract JSON from markdown code blocks if present
            json_match = re.search(r'\{[\s\S]*\}', study_plan_response)
            if json_match:
                study_plan_json = json.loads(json_match.group())
            else:
                # Try parsing the entire response as JSON
                study_plan_json = json.loads(study_plan_response)
            
            # Validate structure
            if "schedule" not in study_plan_json:
                raise ValueError("Response missing 'schedule' key")
            
            # Ensure we have all days from START_DATE to END_DATE
            schedule = study_plan_json.get("schedule", [])
            original_count = len(schedule)
            schedule_dates = {day.get("date"): day for day in schedule}
            
            # Build complete schedule with all days in the date range
            complete_schedule = []
            for expected_day in week_dates:
                if expected_day["date"] in schedule_dates:
                    # Use the day from Gemini response
                    complete_schedule.append(schedule_dates[expected_day["date"]])
                else:
                    # Fill in missing day
                    print(f"Warning: Missing day {expected_day['day_name']} ({expected_day['date']}), adding empty day")
                    complete_schedule.append({
                        "day": expected_day["full_date"],
                        "date": expected_day["date"],
                        "assignments": []
                    })
            
            # Update the schedule in the response
            study_plan_json["schedule"] = complete_schedule
            
            # Log if we had to fill in days
            if original_count < len(week_dates):
                print(f"Info: Received {original_count} days, filled to {len(week_dates)} days to match Canvas date range ({START_DATE} to {END_DATE}).")
            
            return jsonify({
                "status": "success",
                "study_plan": study_plan_json,
                "raw_response": study_plan_response  # Include raw for debugging
            })
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from Gemini: {e}")
            print(f"Raw response: {study_plan_response}")
            # Fallback: return raw response if JSON parsing fails
            return jsonify({
                "status": "success",
                "study_plan": {
                    "schedule": [],
                    "error": "Failed to parse schedule. Raw response provided.",
                    "raw_response": study_plan_response
                }
            })
        
    except Exception as e:
        print(f"Error generating study plan: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/notifications/assignments", methods=["POST"])
def send_assignments_notifications():
    """
    Send Discord notifications for multiple assignments when Generate Study Plan is clicked.
    Uses Discord user ID from settings and Discord bot token from .env.
    """
    try:
        data = request.json
        assignments = data.get("assignments", [])
        
        if not assignments or len(assignments) == 0:
            return jsonify({
                "status": "success",
                "message": "No assignments to notify",
                "notifications_sent": 0
            })
        
        # Get Discord user ID from settings
        discord_user_id = get_user_id_from_settings()
        
        if not discord_user_id:
            return jsonify({
                "status": "error",
                "message": "Discord user ID not found. Please set it via 'My Info' in the app.",
                "error_type": "ValueError"
            }), 400
        
        # Check if Discord bot token is configured
        discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
        if not discord_bot_token:
            return jsonify({
                "status": "error",
                "message": "Discord bot token not configured. Please add DISCORD_BOT_TOKEN to your .env file.",
                "error_type": "ConfigurationError"
            }), 500
        
        # Initialize bot
        try:
            bot = AssignmentReminderBot(user_id=discord_user_id)
        except Exception as e:
            print(f"[NOTIFICATION] ❌ Failed to initialize bot: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "status": "error",
                "message": f"Failed to initialize Discord bot: {str(e)}",
                "error_type": type(e).__name__
            }), 500
        
        # Send notifications for all assignments
        notifications_sent = 0
        failed_notifications = []
        error_details = []
        
        for assignment in assignments:
            try:
                assignment_name = assignment.get("name", "Unnamed Assignment")
                due_date = assignment.get("due_date", "No due date")
                description = assignment.get("description", "")
                priority = assignment.get("priority", "none")
                
                # Create a formatted notification message
                priority_emoji = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🔴"
                }.get(priority, "⚪")
                
                # Build notification message
                message_content = f"🔔 **Assignment Notification**\n\n"
                message_content += f"**{assignment_name}**\n\n"
                message_content += f"📅 **Due Date:** {due_date}\n"
                message_content += f"{priority_emoji} **Priority:** {priority.upper() if priority != 'none' else 'Not Set'}\n"
                
                if description:
                    # Clean and truncate description if needed
                    clean_description = description[:200] + "..." if len(description) > 200 else description
                    message_content += f"\n📝 **Description:** {clean_description}\n"
                
                # Send notification via Discord bot
                print(f"[NOTIFICATION] Attempting to send notification for '{assignment_name}' to user {discord_user_id}")
                success = bot.bot.send_dm(user_id=discord_user_id, content=message_content)
                
                if success:
                    notifications_sent += 1
                    print(f"[NOTIFICATION] ✅ Successfully sent notification for '{assignment_name}'")
                else:
                    error_msg = "Failed to send DM. Check bot configuration and permissions."
                    print(f"[NOTIFICATION] ❌ {error_msg}")
                    error_details.append(error_msg)
                    failed_notifications.append(assignment_name)
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                print(f"[NOTIFICATION] ❌ Error sending notification for assignment {assignment.get('name', 'Unknown')}: {e}")
                import traceback
                traceback.print_exc()
                error_details.append(error_msg)
                failed_notifications.append(assignment.get("name", "Unknown"))
        
        # Return result
        if notifications_sent > 0:
            return jsonify({
                "status": "success",
                "message": f"Sent {notifications_sent} notification(s) to Discord",
                "notifications_sent": notifications_sent,
                "failed_notifications": failed_notifications if failed_notifications else None
            })
        else:
            # Provide more detailed error message
            error_message = "Failed to send any notifications. "
            if error_details:
                error_message += error_details[0] if len(error_details) > 0 else "Check your bot configuration."
            else:
                error_message += "Please check: 1) Bot is in a server with you, 2) DMs are enabled, 3) Bot token is valid"
            
            return jsonify({
                "status": "error",
                "message": error_message,
                "notifications_sent": 0,
                "failed_notifications": failed_notifications,
                "error_details": error_details[0] if error_details else "Unknown error"
            }), 500
        
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": "ValueError"
        }), 400
    except Exception as e:
        print(f"Error sending assignment notification: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }), 500


# ============================================================================
# DISCORD REMINDER API ENDPOINTS
# ============================================================================

@app.route("/reminders/test-now", methods=["GET", "POST"])
def test_reminder_now():
    """
    Send a test reminder immediately to verify Discord bot is working.
    Uses Discord user ID from settings (set via /api/settings).
    POST body with user_id is optional (only for override).
    """
    try:
        # Get user_id from request body (optional override) or settings
        override_user_id = None
        if request.method == "POST":
            data = request.json or {}
            override_user_id = data.get("user_id")
        
        user_id = get_user_id_from_settings(override_user_id)
        
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "Discord user ID not found. Please set it via POST /api/settings with 'discordId' field.",
                "error_type": "ValueError"
            }), 400
        
        # Create a test assignment due in 1 minute
        test_assignment = create_test_assignment(minutes_from_now=1)
        
        # Send immediate reminder
        bot = AssignmentReminderBot(user_id=user_id)
        time_remaining_str = "1 minute"
        success = bot.send_individual_reminder(test_assignment, time_remaining_str)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Test reminder sent immediately to Discord! Check your DMs.",
                "user_id": user_id,
                "test_assignment": {
                    "name": test_assignment["name"],
                    "due_in": "1 minute"
                }
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send test reminder. Check Discord bot configuration.",
                "error_type": "DiscordError"
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }), 500


@app.route("/reminders/test", methods=["GET", "POST"])
def test_reminder_system():
    """
    Test the full reminder system with a test assignment due in 14 minutes.
    Uses Discord user ID from settings (set via /api/settings).
    POST body with user_id is optional (only for override).
    """
    try:
        # Get user_id from request body (optional override) or settings
        override_user_id = None
        if request.method == "POST":
            data = request.json or {}
            override_user_id = data.get("user_id")
        
        user_id = get_user_id_from_settings(override_user_id)
        
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "Discord user ID not found. Please set it via POST /api/settings with 'discordId' field.",
                "error_type": "ValueError"
            }), 400
        
        # Run reminder check with test assignment
        check_and_send_reminders(user_id=user_id, include_test=True, debug=True)
        
        return jsonify({
            "status": "success",
            "message": "Test reminder check completed. Check console for debug output and Discord for reminders.",
            "user_id": user_id,
            "test_assignment_due_in": "14 minutes",
            "note": "The 15-minute reminder should have been sent (it's 1 minute past the 15-minute mark)"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }), 500


@app.route("/reminders/force-check", methods=["GET", "POST"])
def force_check_reminders():
    """
    Manually trigger a reminder check for all upcoming assignments.
    Uses Discord user ID from settings (set via /api/settings).
    POST body with user_id is optional (only for override).
    """
    try:
        # Get user_id from request body (optional override) or settings
        override_user_id = None
        if request.method == "POST":
            data = request.json or {}
            override_user_id = data.get("user_id")
        
        user_id = get_user_id_from_settings(override_user_id)
        
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "Discord user ID not found. Please set it via POST /api/settings with 'discordId' field.",
                "error_type": "ValueError"
            }), 400
        
        # Run reminder check
        check_and_send_reminders(user_id=user_id, include_test=False, debug=False)
        
        return jsonify({
            "status": "success",
            "message": "Reminder check completed. Check console for output.",
            "user_id": user_id,
            "time": datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }), 500


@app.route("/reminders/set-user", methods=["POST"])
def set_scheduled_user():
    """
    Configure which user ID should receive scheduled reminders (runs every minute).
    Also updates USER_SETTINGS with the Discord ID.
    """
    global scheduled_user_id, USER_SETTINGS
    
    try:
        # Get user_id from request body or settings
        data = request.json or {}
        user_id = data.get("user_id")
        
        # If not provided in body, try to get from settings
        if not user_id:
            user_id = get_user_id_from_settings()
        
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "user_id is required. Provide it in the request body or set it via POST /api/settings with 'discordId' field.",
                "error_type": "ValueError"
            }), 400
        
        user_id = str(user_id)
        scheduled_user_id = user_id
        
        # Also update USER_SETTINGS if not already set
        if not USER_SETTINGS.get("discord_id"):
            if not USER_SETTINGS:
                USER_SETTINGS = {}
            USER_SETTINGS["discord_id"] = user_id
        
        return jsonify({
            "status": "success",
            "message": f"Scheduled user ID set to {scheduled_user_id}",
            "user_id": scheduled_user_id,
            "note": "Scheduler will now send reminders to this user"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }), 500


@app.route("/reminders/debug", methods=["GET", "POST"])
def debug_reminders():
    """
    Check system status and optionally test DM sending.
    Uses Discord user ID from settings if not provided in request.
    """
    try:
        # Get user_id from query params (GET), JSON body (POST), or settings
        if request.method == "GET":
            override_user_id = request.args.get("user_id")
        else:
            data = request.json or {}
            override_user_id = data.get("user_id")
        
        user_id = get_user_id_from_settings(override_user_id)
        
        # Check Discord bot token
        discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
        discord_bot_token_set = bool(discord_bot_token)
        
        # Check tracker file
        tracker_file_exists = os.path.exists(tracker_file_path)
        
        # Check scheduler status
        scheduler_running = scheduler.running if hasattr(scheduler, 'running') else True
        
        # Test message sending if user_id psrovided
        test_message_sent = False
        if user_id:
            try:
                bot = AssignmentReminderBot(user_id=user_id)
                test_assignment = create_test_assignment(minutes_from_now=60)
                test_message_sent = bot.send_individual_reminder(test_assignment, "1 hour")
            except Exception as e:
                print(f"Error sending test message: {e}")
                test_message_sent = False
        
        return jsonify({
            "mode": "DM (Bot)",
            "discord_bot_token_set": discord_bot_token_set,
            "scheduled_user_id": scheduled_user_id,
            "user_settings_discord_id": USER_SETTINGS.get("discord_id"),
            "test_user_id": user_id,
            "tracker_file_exists": tracker_file_exists,
            "scheduler_running": scheduler_running,
            "current_time_utc": datetime.now(timezone.utc).isoformat(),
            "test_message_sent": test_message_sent
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }), 500


@app.route("/health", methods=["GET"])
def health_check():
    """
    Check if the server and scheduler are running.
    """
    try:
        scheduler_running = scheduler.running if hasattr(scheduler, 'running') else True
        
        return jsonify({
            "status": "healthy",
            "scheduler_running": scheduler_running
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }), 500


@app.route("/reminders/status", methods=["GET"])
def reminders_status():
    """
    Get status of the reminder system and scheduler.
    """
    try:
        scheduler_running = scheduler.running if hasattr(scheduler, 'running') else True
        jobs = [job.id for job in scheduler.get_jobs()] if hasattr(scheduler, 'get_jobs') else ["check_reminders"]
        
        return jsonify({
            "scheduler_running": scheduler_running,
            "jobs": jobs
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }), 500


if __name__ == "__main__":
    print("Starting Flask app with Flask-APScheduler...")
    print("=" * 60)
    
    # Start the scheduler explicitly
    if not scheduler.running:
        scheduler.start()
        print(f"✓ Flask-APScheduler started")
    else:
        print(f"✓ Flask-APScheduler already running")
    
    print(f"✓ Scheduler configured to run reminder checks every 60 seconds")
    print(f"✓ Job ID: 'check_reminders'")
    
    # Check if user ID is configured
    user_id = get_user_id_from_settings()
    if user_id:
        print(f"✓ Discord user ID configured: {user_id}")
        print(f"✓ Reminders will be sent automatically every 60 seconds")
    else:
        print(f"⚠ No Discord user ID configured yet")
        print(f"  Set it via POST /api/settings with 'discordId' field OR")
        print(f"  Set DISCORD_USER_ID in .env file OR")
        print(f"  Use POST /reminders/set-user to enable scheduled reminders")
    
    # List scheduled jobs
    try:
        jobs = scheduler.get_jobs()
        print(f"✓ Active scheduled jobs: {len(jobs)}")
        for job in jobs:
            try:
                interval = job.trigger.interval_length if hasattr(job.trigger, 'interval_length') else 'N/A'
                print(f"  - {job.id}: runs every {interval} seconds")
            except:
                print(f"  - {job.id}: scheduled")
    except Exception as e:
        print(f"⚠ Could not list jobs: {e}")
    
    print("=" * 60)
    print("Flask app starting...")
    app.run(debug=True, port=5000, use_reloader=False)  # use_reloader=False to avoid duplicate schedulers
