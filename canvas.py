import requests
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo # For Python 3.9+
# For Python versions < 3.9, you would typically use 'pytz' library:
# import pytz

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


def fetch_canvas_assignments():
    """
    Fetches Canvas assignments from all user's courses within a specified date range.
    """
    all_assignments = []
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }

    start_dt = datetime.fromisoformat(START_DATE)
    end_dt = datetime.fromisoformat(END_DATE)

    courses = get_user_courses()

    if not courses:
        print("No courses found or unable to fetch courses. Cannot retrieve assignments.")
        return

    print(f"Fetching assignments from {START_DATE} to {END_DATE} for all courses...")

    for course in courses:
        course_id = course.get("id")
        course_name = course.get("name", f"Course {course_id}")
        if not course_id:
            continue

        # Construct the API URL for course assignments
        api_url = f"https://{CANVAS_DOMAIN}/api/v1/courses/{course_id}/assignments"
        params = {
            "per_page": 100,
            "bucket": "upcoming" # Fetch upcoming assignments, then filter by date
        }

        try:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status()
            course_assignments = response.json()

            for assignment in course_assignments:
                due_at_str = assignment.get("due_at")
                if due_at_str:
                    try:
                        due_dt = datetime.fromisoformat(due_at_str.rstrip("Z"))
                        if start_dt <= due_dt <= end_dt:
                            assignment["course_name"] = course_name # Add course name for display
                            all_assignments.append(assignment)
                    except ValueError:
                        pass # Ignore assignments with unparseable due dates

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred for course {course_name} ({course_id}): {http_err}")
        except requests.exceptions.RequestException as err:
            print(f"An error occurred for course {course_name} ({course_id}): {err}")
        except json.JSONDecodeError:
            print(f"Failed to decode assignment response for course {course_name} ({course_id}).")

    if not all_assignments:
        print("No assignments found in this date range across all your courses.")
        return []

    formatted_assignments = []
    for assignment in all_assignments:
        title = assignment.get("name", "No Title")
        
        due_date_str = assignment.get("due_at", "No Due Date")
        formatted_due_date = "No Due Date"
        if due_date_str and due_date_str != "No Due Date":
            try:
                # Parse the ISO 8601 date string. It should be timezone-aware (UTC).
                due_date_utc = datetime.fromisoformat(due_date_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                
                # Define the local timezone (America/Los_Angeles is UTC-8)
                # For Python 3.9+
                local_timezone = ZoneInfo("America/Los_Angeles")
                # For older Python versions with pytz:
                # local_timezone = pytz.timezone("America/Los_Angeles")

                # Convert UTC due date to local timezone
                due_date_local = due_date_utc.astimezone(local_timezone)
                
                formatted_due_date = due_date_local.strftime("%A, %B %d at %I:%M %p")
            except ValueError:
                pass # Keep the original string if parsing fails
            except Exception as e:
                print(f"Error converting timezone for {title}: {e}")
        
        formatted_assignments.append({
            "name": title,
            "due_date": formatted_due_date
        })
    
    return formatted_assignments

# Run the function
def get_user_courses():
    """
    Fetches all courses the user is enrolled in.
    """
    api_url = f"https://{CANVAS_DOMAIN}/api/v1/courses"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }
    params = {
        "enrollment_state": "active", # Only get active courses
        "per_page": 100
    }

    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        courses = response.json()
        print(f"Found {len(courses)} active courses.")
        return courses
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while fetching courses: {http_err}")
        print("Please check your API Token and Canvas Domain.")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred while fetching courses: {err}")
    except json.JSONDecodeError:
        print("Failed to decode course response from Canvas. The API may be down.")
    return []

if __name__ == "__main__":
    assignments_array = fetch_canvas_assignments()
    if assignments_array:
        print(json.dumps(assignments_array, indent=2))
