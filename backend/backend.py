from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- PLEASE EDIT THESE VALUES ---
CANVAS_DOMAIN = "coastdistrict.instructure.com"  # Replace with your school's Canvas domain
API_TOKEN = "2352~hNJYEBRcZk3TkEeGxFwz4vLymAxe23fHQBRxCvaXTKtJecZQPXfHCCEzhMnZVk7L"  # Replace with the Access Token you generated
START_DATE = "2025-11-08"  # Set your desired start date (YYYY-MM-DD)
END_DATE = "2025-11-15"    # Set your desired end date (YYYY-MM-DD)

# Optional: Set a specific course ID.
# Leave as None to get assignments from ALL your courses.
# COURSE_ID = "12345"
COURSE_ID = None
# ----------------------------------


def get_user_courses(canvas_domain: str, api_token: str):
    """
    Fetch all active courses for the user from Canvas.
    """
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

    start_dt = datetime.fromisoformat(START_DATE)
    end_dt = datetime.fromisoformat(END_DATE)
    courses = get_user_courses(canvas_domain, api_token)

    all_assignments = []
    headers = {"Authorization": f"Bearer {api_token}"}

    for course in courses:
        course_id = course.get("id")
        course_name = course.get("name", f"Course {course_id}")
        if not course_id:
            continue

        api_url = f"https://{canvas_domain}/api/v1/courses/{course_id}/assignments"
        params = {"per_page": 100, "bucket": "upcoming"}

        try:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            assignments = response.json()

            for assignment in assignments:
                due_at = assignment.get("due_at")
                if due_at:
                    try:
                        due_dt = datetime.fromisoformat(due_at.rstrip("Z"))
                        if start_dt <= due_dt <= end_dt:
                            assignment["course_name"] = course_name
                            all_assignments.append(assignment)
                    except ValueError:
                        continue
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
            "due_date": formatted_due_date
        })

    return formatted_assignments


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
    """
    assignments = fetch_canvas_assignments()
    return jsonify(assignments)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
