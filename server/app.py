from flask import Flask, request
from flask_apscheduler import APScheduler
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

CANVAS_API_KEY = os.getenv("CANVAS_API_KEY")

app = Flask(__name__)

# Configure APScheduler
app.config['SCHEDULER_API_ENABLED'] = True  # Enable API to manage jobs (optional)
app.config['SCHEDULER_TIMEZONE'] = 'UTC'    # Use UTC for all scheduled jobs

# Initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)

# Import reminder service
from reminder_service import check_and_send_reminders


# Store user_id for scheduled reminders (can be set via API or env)
import os
from dotenv import load_dotenv
load_dotenv()

SCHEDULED_USER_ID = os.getenv("DISCORD_USER_ID")  # Optional: can be set in env or via API

@scheduler.task('interval', id='check_reminders', seconds=60, max_instances=1)
def check_reminders_job():
    """
    Scheduled job that runs every minute to check for reminders.
    max_instances=1 ensures only one instance runs at a time.
    """
    try:
        if not SCHEDULED_USER_ID:
            print(f"[SCHEDULER] Skipping - no user_id configured. Set DISCORD_USER_ID in .env or use /reminders/set-user endpoint")
            return
        
        print(f"[SCHEDULER] Running reminder check at {datetime.now()}")
        # Run without debug to avoid too much output, but can enable for troubleshooting
        check_and_send_reminders(user_id=SCHEDULED_USER_ID, include_test=False, debug=False)
        print(f"[SCHEDULER] Reminder check completed")
    except Exception as e:
        print(f"[SCHEDULER ERROR] Error in reminder job: {e}")
        import traceback
        traceback.print_exc()


@app.route('/')
def index():
    return {"message": "Hello, World!"}


@app.route('/health')
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running if scheduler else False
    }


@app.route('/reminders/status')
def reminders_status():
    """Get status of reminder system."""
    return {
        "scheduler_running": scheduler.running if scheduler else False,
        "jobs": [job.id for job in scheduler.get_jobs()] if scheduler else []
    }


@app.route('/reminders/test', methods=['POST'])
def test_reminders():
    """
    Test endpoint to trigger reminder check with a test assignment.
    Creates a fake assignment due in 14 minutes to test the system.
    Requires user_id in JSON body.
    
    Usage: POST /reminders/test
    Body: {"user_id": "123456789012345678"}
    """
    from reminder_service import check_and_send_reminders, create_test_assignment
    from reminder_service import tracker
    from discord_reminder import AssignmentReminderBot
    from datetime import datetime, timedelta
    from dateutil.parser import parse
    from dateutil.tz import UTC
    from reminder_service import calculate_reminder_times, format_time_remaining
    
    # Get user_id from JSON body
    data = request.get_json()
    if not data or 'user_id' not in data:
        return {
            "status": "error",
            "message": "user_id is required in request body",
            "example": {"user_id": "123456789012345678"}
        }, 400
    
    user_id = str(data['user_id'])
    
    try:
        print("\n" + "="*50)
        print("🧪 TEST: Starting reminder test")
        print("="*50)
        
        # Initialize bot for this user
        bot = AssignmentReminderBot(user_id=user_id)
        
        # Create test assignment due in 14 minutes (so 15-min reminder is 1 minute ago, should trigger)
        test_assignment = create_test_assignment(minutes_from_now=14)
        current_time = datetime.now(UTC)
        due_time = parse(test_assignment['due_at']).astimezone(UTC)
        
        print(f"🧪 TEST: Created test assignment: {test_assignment['name']}")
        print(f"🧪 TEST: Due at: {due_time}")
        print(f"🧪 TEST: Current time: {current_time}")
        print(f"🧪 TEST: Minutes until due: {(due_time - current_time).total_seconds() / 60:.1f}")
        print(f"🧪 TEST: Sending to user ID: {user_id}")
        
        # Run reminder check with test assignment and debug output
        check_and_send_reminders(user_id=user_id, include_test=True, debug=True)
        
        # Also manually check if we should send the 15-minute reminder
        reminder_times = calculate_reminder_times(due_time)
        fifteen_min_reminder = reminder_times[-1]  # 15 minutes before
        
        time_since_reminder = (current_time - fifteen_min_reminder).total_seconds() / 60
        print(f"\n🧪 TEST: 15-minute reminder was scheduled for: {fifteen_min_reminder}")
        print(f"🧪 TEST: Time since 15-min reminder: {time_since_reminder:.1f} minutes")
        
        # If the 15-minute reminder time has passed (within 3 minutes), send it manually
        if -3 <= time_since_reminder <= 3:
            if not tracker.is_reminder_sent(test_assignment['id'], fifteen_min_reminder):
                print(f"🧪 TEST: Sending 15-minute reminder manually...")
                time_remaining = due_time - current_time
                time_remaining_str = format_time_remaining(time_remaining)
                success = bot.send_individual_reminder(test_assignment, time_remaining_str)
                
                if success:
                    tracker.mark_reminder_sent(test_assignment['id'], fifteen_min_reminder, due_time)
                    print(f"✅ TEST: Manually sent 15-minute reminder!")
                else:
                    print(f"❌ TEST: Failed to send reminder manually")
        
        print("="*50 + "\n")
        
        return {
            "status": "success",
            "message": "Test reminder check completed. Check console for debug output and Discord for reminders.",
            "user_id": user_id,
            "test_assignment_due_in": "14 minutes",
            "note": "The 15-minute reminder should have been sent (it's 1 minute past the 15-minute mark)"
        }
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }, 500


@app.route('/reminders/test-now', methods=['POST'])
def test_reminders_now():
    """
    Test endpoint to send a reminder immediately for a test assignment.
    Creates a fake assignment due in 1 minute to test immediate reminder.
    Requires user_id in JSON body.
    
    Usage: POST /reminders/test-now
    Body: {"user_id": "123456789012345678"}
    """
    from reminder_service import create_test_assignment
    from discord_reminder import AssignmentReminderBot
    
    # Get user_id from JSON body
    data = request.get_json()
    if not data or 'user_id' not in data:
        return {
            "status": "error",
            "message": "user_id is required in request body",
            "example": {"user_id": "123456789012345678"}
        }, 400
    
    user_id = str(data['user_id'])
    
    try:
        # Initialize bot for this user
        bot = AssignmentReminderBot(user_id=user_id)
        
        # Create test assignment due in 1 minute
        test_assignment = create_test_assignment(minutes_from_now=1)
        
        print(f"🧪 TEST: Sending immediate reminder for test assignment")
        print(f"🧪 TEST: Assignment: {test_assignment['name']}")
        print(f"🧪 TEST: Due in: 1 minute")
        print(f"🧪 TEST: Sending DM to user ID: {user_id}")
        
        # Send reminder immediately
        success = bot.send_individual_reminder(test_assignment, "1 minute")
        
        if success:
            print(f"✅ TEST: Reminder sent successfully to Discord!")
            return {
                "status": "success",
                "message": "Test reminder sent immediately to Discord! Check your DMs.",
                "user_id": user_id,
                "test_assignment": {
                    "name": test_assignment['name'],
                    "due_in": "1 minute"
                }
            }
        else:
            print(f"❌ TEST: Failed to send reminder")
            return {
                "status": "error",
                "message": "Failed to send test reminder. Check Discord bot token, user ID, and console logs.",
                "debug": "Check that DISCORD_BOT_TOKEN is set correctly in .env file"
            }, 500
    except Exception as e:
        print(f"❌ TEST: Exception: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }, 500


@app.route('/reminders/debug', methods=['GET', 'POST'])
def debug_reminders():
    """
    Debug endpoint to check reminder system status and test Discord bot.
    Optional user_id in JSON body (POST) or query parameter (GET) to test DM sending.
    
    Usage: 
    - GET /reminders/debug?user_id=123456789012345678
    - POST /reminders/debug with body: {"user_id": "123456789012345678"}
    """
    from reminder_service import tracker
    from discord_reminder import DISCORD_BOT_TOKEN
    import os
    
    # Support both GET (query param) and POST (JSON body) for flexibility
    if request.method == 'POST':
        data = request.get_json() or {}
        user_id = data.get('user_id')
    else:
        user_id = request.args.get('user_id')
    
    scheduled_user_id = SCHEDULED_USER_ID
    
    debug_info = {
        "mode": "DM (Bot)",
        "discord_bot_token_set": bool(DISCORD_BOT_TOKEN),
        "scheduled_user_id": scheduled_user_id if scheduled_user_id else "Not set (scheduler disabled)",
        "test_user_id": user_id if user_id else "Not provided",
        "tracker_file_exists": os.path.exists("reminders_sent.json"),
        "scheduler_running": scheduler.running if scheduler else False,
        "current_time_utc": datetime.utcnow().isoformat(),
    }
    
    # Try to send a test message if user_id is provided
    if user_id:
        try:
            from discord_reminder import DiscordBot
            bot = DiscordBot()
            test_message = "🧪 **Test Message**\n\nThis is a test to verify Discord bot DM is working."
            test_success = bot.send_dm(user_id, test_message)
            debug_info["test_message_sent"] = test_success
            if not test_success:
                debug_info["test_message_error"] = "Failed to send DM (check console for details)"
        except Exception as e:
            debug_info["test_message_error"] = str(e)
            import traceback
            debug_info["test_message_traceback"] = traceback.format_exc()
    else:
        debug_info["test_message_note"] = "Provide user_id as query parameter (GET) or in JSON body (POST) to test DM sending"
    
    return debug_info


@app.route('/reminders/force-check', methods=['POST'])
def force_check():
    """
    Force an immediate reminder check (useful for testing).
    Requires user_id in JSON body.
    
    Usage: POST /reminders/force-check
    Body: {"user_id": "123456789012345678"}
    """
    from reminder_service import check_and_send_reminders
    
    # Get user_id from JSON body
    data = request.get_json()
    if not data or 'user_id' not in data:
        return {
            "status": "error",
            "message": "user_id is required in request body",
            "example": {"user_id": "123456789012345678"}
        }, 400
    
    user_id = str(data['user_id'])
    
    try:
        print(f"\n[FORCE CHECK] Manual reminder check triggered at {datetime.now()}")
        check_and_send_reminders(user_id=user_id, include_test=False, debug=True)
        return {
            "status": "success",
            "message": "Reminder check completed. Check console for output.",
            "user_id": user_id,
            "time": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"[FORCE CHECK ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }, 500


@app.route('/reminders/set-user', methods=['POST'])
def set_scheduled_user():
    """
    Set the user ID for scheduled reminders.
    This allows the scheduler to send reminders to a specific user.
    
    Usage: POST /reminders/set-user
    Body: {"user_id": "123456789012345678"}
    """
    global SCHEDULED_USER_ID
    
    data = request.get_json()
    if not data or 'user_id' not in data:
        return {
            "status": "error",
            "message": "user_id is required in request body",
            "example": {"user_id": "123456789012345678"}
        }, 400
    
    user_id = str(data['user_id'])
    SCHEDULED_USER_ID = user_id
    
    print(f"[CONFIG] Set scheduled user ID to: {user_id}")
    
    return {
        "status": "success",
        "message": f"Scheduled user ID set to {user_id}",
        "user_id": user_id,
        "note": "Scheduler will now send reminders to this user"
    }


if __name__ == '__main__':
    # Start the scheduler
    scheduler.start()
    
    # Run the Flask app
    app.run(debug=True, use_reloader=False)  # use_reloader=False to avoid duplicate scheduler instances