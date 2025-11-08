# Time-Based Reminder System

This document explains the time-based reminder system that sends Discord notifications for assignments 1 hour before they're due, then every 15 minutes after that.

## Architecture

The reminder system consists of several components:

### Files

1. **`reminder_tracker.py`** - Manages state of sent reminders to prevent duplicates
   - Stores reminder state in `reminders_sent.json`
   - Tracks which reminders have been sent for each assignment
   - Cleans up old reminders automatically

2. **`reminder_service.py`** - Core reminder checking logic
   - Checks for assignments due soon
   - Calculates reminder times (1 hour, 45 min, 30 min, 15 min before due)
   - Sends individual reminders via Discord

3. **`discord_reminder.py`** - Discord webhook integration
   - `send_individual_reminder()` - Sends single assignment reminders
   - `send_assignment_reminder()` - Sends daily summary (existing)

4. **`app.py`** - Flask app with APScheduler integration
   - Runs reminder checks every minute
   - Provides health check endpoints

## How It Works

1. **Scheduler**: APScheduler runs a job every 60 seconds
2. **Check**: The job calls `check_and_send_reminders()`
3. **Fetch**: Gets all assignments due in the next 7 days from Canvas
4. **Calculate**: For each assignment, calculates reminder times:
   - 1 hour before due time
   - 45 minutes before
   - 30 minutes before
   - 15 minutes before
5. **Send**: If current time is within a 2-minute window of a reminder time, sends the reminder
6. **Track**: Marks reminder as sent to prevent duplicates
7. **Cleanup**: Periodically removes old reminders from tracking

## Installation

1. Install required packages:
```bash
pip install flask-apscheduler requests python-dateutil python-dotenv
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

2. Make sure your `.env` file has:
```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
CANVAS_API_KEY=your_canvas_api_key
```

## Running

### Development
```bash
python app.py
```

The Flask app will start and the scheduler will begin checking for reminders every minute.

### Production
Use a production WSGI server like Gunicorn:
```bash
gunicorn app:app
```

**Note**: The scheduler runs in the same process as Flask, so it will work with Gunicorn workers. However, for production, consider using a single worker or a separate scheduler process.

## Reminder Timing

Reminders are sent at:
- **1 hour** before due time
- **45 minutes** before due time
- **30 minutes** before due time
- **15 minutes** before due time

The system checks every minute and sends reminders if the current time is within a 2-minute window of the scheduled reminder time. This accounts for polling delays.

## Reminder Messages

Individual reminders include:
- Assignment name
- Course name
- Time remaining until due
- Due date and time
- Assignment description (truncated)
- Color-coded by urgency:
  - 🟠 Orange: 1 hour remaining
  - 🔴 Red: 30-45 minutes remaining
  - 🔥 Dark Red: 15 minutes or less

## State Management

Reminders are tracked in `reminders_sent.json`:
```json
{
  "assignment_id": {
    "due_time": "2025-01-15T14:00:00Z",
    "reminders_sent": [
      "2025-01-15T13:00:00Z",
      "2025-01-15T13:15:00Z"
    ],
    "last_updated": "2025-01-15T13:15:00Z"
  }
}
```

This prevents duplicate reminders if the system restarts or if there are timing issues.

## API Endpoints

### Health Check
```
GET /health
```
Returns scheduler status.

### Reminders Status
```
GET /reminders/status
```
Returns detailed status of the reminder system.

## Troubleshooting

### Reminders not sending
1. Check that `DISCORD_WEBHOOK_URL` is set in `.env`
2. Verify the webhook URL is valid and not expired
3. Check Flask app logs for errors
4. Verify scheduler is running: `GET /health`

### Duplicate reminders
- The tracker should prevent this, but if it happens, check `reminders_sent.json`
- Delete the file to reset (will cause duplicates until state rebuilds)

### Scheduler not running
- Make sure `scheduler.start()` is called before `app.run()`
- Check that Flask-APScheduler is installed
- Verify no import errors in logs

## Configuration

### Change Reminder Times
Edit `reminder_service.py`:
```python
def calculate_reminder_times(due_datetime):
    return [
        due_datetime - timedelta(hours=1),    # Change this
        due_datetime - timedelta(minutes=45), # Change this
        # Add more times here
    ]
```

### Change Check Frequency
Edit `app.py`:
```python
@scheduler.task('interval', id='check_reminders', seconds=60)  # Change 60 to desired seconds
```

### Change Cleanup Frequency
Edit `reminder_service.py`:
```python
tracker.cleanup_old_reminders(days_old=1)  # Change days_old
```

## File Structure

```
server/
├── app.py                    # Flask app with scheduler
├── reminder_service.py       # Reminder checking logic
├── reminder_tracker.py       # State management
├── discord_reminder.py       # Discord webhook integration
├── canvas.py                 # Canvas API functions
├── reminders_sent.json       # Reminder state (auto-generated)
└── requirements.txt          # Python dependencies
```

## Notes

- The scheduler runs in UTC timezone
- All assignment due times are converted to UTC for consistency
- The system automatically handles timezone conversions
- Reminders are sent as individual Discord messages (not grouped)
- The system only checks assignments due in the next 7 days (configurable in `canvas.py`)

