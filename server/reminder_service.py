"""
Reminder Service - Checks for assignments due soon and sends reminders.
Designed to run as a scheduled job via Flask-APScheduler.
"""
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.tz import UTC
from canvas import get_assignments_next_week
from discord_reminder import AssignmentReminderBot
from reminder_tracker import ReminderTracker

# Initialize tracker (singleton pattern)
tracker = ReminderTracker()

# Bot will be initialized per-request with user_id
# For scheduled reminders, user_id should be passed to check_and_send_reminders
bot = None  # Will be initialized when needed


def calculate_reminder_times(due_datetime):
    """
    Calculate all reminder times for an assignment.
    
    Args:
        due_datetime: Datetime when assignment is due (timezone-aware)
    
    Returns:
        List of datetimes when reminders should be sent
    """
    return [
        due_datetime - timedelta(hours=1),    # 1 hour before
        due_datetime - timedelta(minutes=45), # 45 minutes before
        due_datetime - timedelta(minutes=30), # 30 minutes before
        due_datetime - timedelta(minutes=15), # 15 minutes before
    ]


def should_send_reminder(reminder_time, current_time, assignment_id, due_time=None):
    """
    Check if a reminder should be sent now.
    
    Args:
        reminder_time: When the reminder should be sent
        current_time: Current time
        assignment_id: Assignment ID for tracking
        due_time: Optional due time for the assignment (for special handling)
    
    Returns:
        True if reminder should be sent, False otherwise
    """
    # Calculate time difference
    time_diff = (current_time - reminder_time).total_seconds()
    
    # Special case: If assignment is due within 15 minutes, send 15-min reminder immediately
    # This handles test cases and ensures reminders aren't missed
    if due_time:
        minutes_until_due = (due_time - current_time).total_seconds() / 60
        # If due in 15 minutes or less, and this is the 15-minute reminder, send it
        if 14 <= minutes_until_due <= 16:
            # This is likely the 15-minute reminder window
            if abs(time_diff) < 120:  # Within 2 minutes of reminder time
                # Check if we've already sent this reminder
                if not tracker.is_reminder_sent(assignment_id, reminder_time):
                    return True
    
    # If reminder time is in the future, don't send yet
    # But allow a small buffer (60 seconds) for timing precision
    if time_diff < -60:  # More than 60 seconds in the future
        return False  # Too early
    
    # Check if we're within a 3-minute window (to account for polling delay)
    # This means we'll send if we're up to 3 minutes past the reminder time
    if time_diff > 180:  # 3 minutes
        return False  # Too late (missed the window)
    
    # Check if we've already sent this reminder
    if tracker.is_reminder_sent(assignment_id, reminder_time):
        return False
    
    return True


def format_time_remaining(time_remaining):
    """
    Format time remaining as a human-readable string.
    
    Args:
        time_remaining: Timedelta object
    
    Returns:
        Formatted string (e.g., "1 hour", "45 minutes", "30 minutes")
    """
    total_seconds = int(time_remaining.total_seconds())
    
    if total_seconds >= 3600:  # 1 hour or more
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if minutes > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} and {minutes} minute{'s' if minutes > 1 else ''}"
        return f"{hours} hour{'s' if hours > 1 else ''}"
    elif total_seconds >= 60:  # Minutes
        minutes = total_seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:  # Less than a minute
        return f"{total_seconds} second{'s' if total_seconds > 1 else ''}"


def create_test_assignment(minutes_from_now=16):
    """
    Create a test assignment for testing the reminder system.
    
    Args:
        minutes_from_now: Minutes from now when assignment is due (default: 16)
    
    Returns:
        Dictionary representing a test assignment
    """
    current_time = datetime.now(UTC)
    due_time = current_time + timedelta(minutes=minutes_from_now)
    
    return {
        'id': 'test_assignment_001',
        'name': '🧪 TEST Assignment - Please Ignore',
        'course_id': 999999,
        'course_name': 'Test Course',
        'due_at': due_time.isoformat(),
        'description': 'This is a test assignment created to test the reminder system. You can safely ignore this.'
    }


def check_and_send_reminders(user_id: str, include_test=False, debug=False):
    """
    Main function to check for assignments due soon and send reminders.
    This function is designed to be called by the scheduler.
    
    Args:
        user_id: Discord user ID to send reminders to (required)
        include_test: If True, includes a test assignment due in 16 minutes
        debug: If True, prints detailed debugging information
    """
    if not user_id:
        raise ValueError("user_id must be provided")
    
    # Initialize bot for this user
    bot = AssignmentReminderBot(user_id=user_id)
    
    current_time = datetime.now(UTC)
    
    print(f"[REMINDER CHECK] Starting at {current_time} (user_id={user_id}, debug={debug}, include_test={include_test})")
    
    try:
        # Get all upcoming assignments
        print("[REMINDER CHECK] Fetching assignments from Canvas...")
        assignments = get_assignments_next_week()
        print(f"[REMINDER CHECK] Fetched {len(assignments) if assignments else 0} assignment(s) from Canvas")
        
        # Add test assignment if requested
        if include_test:
            # Use 14 minutes so the 15-minute reminder is 1 minute ago (should trigger)
            test_assignment = create_test_assignment(minutes_from_now=14)
            if not assignments:
                assignments = []
            assignments.append(test_assignment)
            print(f"🧪 TEST MODE: Added test assignment due in 14 minutes")
            if debug:
                print(f"[DEBUG] Test assignment due at: {test_assignment['due_at']}")
        
        if not assignments:
            print("[REMINDER CHECK] No assignments to process")
            if debug:
                print("[DEBUG] No assignments found")
            return
        
        print(f"[REMINDER CHECK] Processing {len(assignments)} assignment(s)")
        
        if debug:
            print(f"[DEBUG] Found {len(assignments)} assignment(s) to check")
        
        reminders_sent_count = 0
        
        for assignment in assignments:
            assignment_id = assignment.get('id')
            due_at = assignment.get('due_at')
            assignment_name = assignment.get('name', 'Unknown')
            
            if not due_at or not assignment_id:
                if debug:
                    print(f"[DEBUG] Skipping assignment '{assignment_name}': missing due_at or id")
                continue
            
            try:
                # Parse due time
                due_time = parse(due_at)
                if due_time.tzinfo:
                    due_time = due_time.astimezone(UTC)
                else:
                    due_time = due_time.replace(tzinfo=UTC)
                
                # Skip if assignment is already past due
                if due_time < current_time:
                    if debug:
                        print(f"[DEBUG] Skipping assignment '{assignment_name}': already past due")
                    continue
                
                # Calculate time until due
                time_until_due = (due_time - current_time).total_seconds() / 60  # minutes
                
                if debug:
                    print(f"[DEBUG] Assignment '{assignment_name}' due in {time_until_due:.1f} minutes")
                
                # Calculate reminder times
                reminder_times = calculate_reminder_times(due_time)
                
                if debug:
                    print(f"[DEBUG] Reminder times for '{assignment_name}':")
                    for rt in reminder_times:
                        minutes_until_reminder = (rt - current_time).total_seconds() / 60
                        print(f"  - {rt.strftime('%H:%M:%S')} ({minutes_until_reminder:.1f} minutes from now)")
                
                # Check each reminder time
                for reminder_time in reminder_times:
                    should_send = should_send_reminder(reminder_time, current_time, assignment_id, due_time)
                    
                    if debug:
                        minutes_until = (reminder_time - current_time).total_seconds() / 60
                        already_sent = tracker.is_reminder_sent(assignment_id, reminder_time)
                        print(f"[DEBUG]   Reminder at {reminder_time.strftime('%H:%M:%S')}: should_send={should_send}, minutes_until={minutes_until:.1f}, already_sent={already_sent}")
                        if not should_send and minutes_until > -2:  # Within 2 minutes
                            print(f"[DEBUG]     Why not sending: time_diff={minutes_until:.1f} min, already_sent={already_sent}")
                    
                    if should_send:
                        # Calculate time remaining
                        time_remaining = due_time - current_time
                        time_remaining_str = format_time_remaining(time_remaining)
                        
                        if debug:
                            print(f"[DEBUG]   SENDING REMINDER for '{assignment_name}' - {time_remaining_str} remaining")
                        
                        # Send reminder
                        success = bot.send_individual_reminder(assignment, time_remaining_str)
                        
                        if success:
                            # Mark as sent
                            tracker.mark_reminder_sent(assignment_id, reminder_time, due_time)
                            reminders_sent_count += 1
                            print(f"✅ Sent reminder for assignment '{assignment_name}' - {time_remaining_str} remaining")
                        else:
                            print(f"❌ Failed to send reminder for assignment '{assignment_name}'")
                            if debug:
                                print(f"[DEBUG]   Discord webhook may be invalid or unreachable")
            
            except Exception as e:
                print(f"Error processing assignment {assignment_id}: {e}")
                if debug:
                    import traceback
                    traceback.print_exc()
                continue
        
        print(f"[REMINDER CHECK] Completed. Sent {reminders_sent_count} reminder(s)")
        if debug:
            print(f"[DEBUG] Total reminders sent: {reminders_sent_count}")
        
        # Cleanup old reminders (run once per check to avoid too frequent cleanup)
        if reminders_sent_count > 0 or current_time.minute == 0:  # Cleanup on the hour
            tracker.cleanup_old_reminders(days_old=1)
    
    except Exception as e:
        print(f"[REMINDER CHECK ERROR] Error in check_and_send_reminders: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise to ensure errors are visible

