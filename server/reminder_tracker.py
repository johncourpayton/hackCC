"""
Reminder Tracker - Manages state of sent reminders to prevent duplicates.
Uses JSON file for persistence.
"""
import json
import os
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.tz import UTC

TRACKER_FILE = "reminders_sent.json"


class ReminderTracker:
    """Tracks which reminders have been sent to avoid duplicates."""
    
    def __init__(self, tracker_file=None):
        """
        Initialize the reminder tracker.
        
        Args:
            tracker_file: Path to JSON file for persistence (default: reminders_sent.json)
        """
        self.tracker_file = tracker_file or TRACKER_FILE
        self.data = self.load_data()
    
    def load_data(self):
        """Load reminder tracking data from JSON file."""
        if os.path.exists(self.tracker_file):
            try:
                with open(self.tracker_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading tracker file: {e}")
                return {}
        return {}
    
    def save_data(self):
        """Save reminder tracking data to JSON file."""
        try:
            with open(self.tracker_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"Error saving tracker file: {e}")
    
    def is_reminder_sent(self, assignment_id, reminder_time):
        """
        Check if a reminder has already been sent.
        
        Args:
            assignment_id: Canvas assignment ID
            reminder_time: Datetime when reminder should be sent
        
        Returns:
            True if reminder was already sent, False otherwise
        """
        assignment_id_str = str(assignment_id)
        reminder_time_str = reminder_time.isoformat()
        
        if assignment_id_str not in self.data:
            return False
        
        return reminder_time_str in self.data[assignment_id_str].get('reminders_sent', [])
    
    def mark_reminder_sent(self, assignment_id, reminder_time, due_time=None):
        """
        Mark a reminder as sent.
        
        Args:
            assignment_id: Canvas assignment ID
            reminder_time: Datetime when reminder was sent
            due_time: Optional due time for the assignment
        """
        assignment_id_str = str(assignment_id)
        reminder_time_str = reminder_time.isoformat()
        
        if assignment_id_str not in self.data:
            self.data[assignment_id_str] = {
                'reminders_sent': [],
                'last_updated': datetime.now(UTC).isoformat()
            }
        
        if due_time:
            self.data[assignment_id_str]['due_time'] = due_time.isoformat()
        
        if reminder_time_str not in self.data[assignment_id_str]['reminders_sent']:
            self.data[assignment_id_str]['reminders_sent'].append(reminder_time_str)
            self.data[assignment_id_str]['last_updated'] = datetime.now(UTC).isoformat()
            self.save_data()
    
    def cleanup_old_reminders(self, days_old=1):
        """
        Remove reminders for assignments that are more than X days past due.
        
        Args:
            days_old: Number of days past due before cleanup (default: 1)
        """
        current_time = datetime.now(UTC)
        cutoff_time = current_time - timedelta(days=days_old)
        
        to_remove = []
        for assignment_id, data in self.data.items():
            # Check if assignment is past due
            due_time_str = data.get('due_time')
            if due_time_str:
                try:
                    due_time = parse(due_time_str)
                    if due_time.tzinfo:
                        due_time = due_time.astimezone(UTC)
                    else:
                        due_time = due_time.replace(tzinfo=UTC)
                    
                    # If due time is more than days_old ago, remove it
                    if due_time < cutoff_time:
                        to_remove.append(assignment_id)
                except (ValueError, TypeError):
                    # If we can't parse the due time, check last_updated
                    last_updated_str = data.get('last_updated')
                    if last_updated_str:
                        try:
                            last_updated = parse(last_updated_str)
                            if last_updated.tzinfo:
                                last_updated = last_updated.astimezone(UTC)
                            else:
                                last_updated = last_updated.replace(tzinfo=UTC)
                            
                            if last_updated < cutoff_time:
                                to_remove.append(assignment_id)
                        except (ValueError, TypeError):
                            pass
        
        # Remove old assignments
        for assignment_id in to_remove:
            del self.data[assignment_id]
        
        if to_remove:
            self.save_data()
            print(f"Cleaned up {len(to_remove)} old reminder entries")

