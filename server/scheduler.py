"""
Scheduler script to run Discord reminders automatically.
Can be run as a cron job or Windows Task Scheduler task.
"""
import time
import schedule
from datetime import datetime
from discord_reminder import AssignmentReminderBot

def send_daily_reminders():
    """Send daily assignment reminders."""
    print(f"[{datetime.now()}] Sending daily assignment reminders...")
    try:
        bot = AssignmentReminderBot()
        success = bot.send_assignment_reminder()
        if success:
            print(f"[{datetime.now()}] ✅ Reminders sent successfully!")
        else:
            print(f"[{datetime.now()}] ❌ Failed to send reminders")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")

def main():
    """Main scheduler function."""
    print("Discord Reminder Scheduler Started")
    print("=" * 50)
    
    # Schedule reminders
    # Send reminders every day at 9:00 AM
    schedule.every().day.at("09:00").do(send_daily_reminders)
    
    # You can also schedule for specific days:
    # schedule.every().monday.at("09:00").do(send_daily_reminders)
    # schedule.every().wednesday.at("09:00").do(send_daily_reminders)
    # schedule.every().friday.at("09:00").do(send_daily_reminders)
    
    # Or multiple times per day:
    # schedule.every().day.at("09:00").do(send_daily_reminders)
    # schedule.every().day.at("18:00").do(send_daily_reminders)
    
    print("Scheduled reminders:")
    print("  - Daily at 9:00 AM")
    print("\nPress Ctrl+C to stop the scheduler")
    print("=" * 50)
    
    # Send initial reminder
    send_daily_reminders()
    
    # Run scheduler
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\nScheduler stopped.")

if __name__ == "__main__":
    # Install schedule package: pip install schedule
    try:
        import schedule
    except ImportError:
        print("Error: 'schedule' package not installed.")
        print("Install it with: pip install schedule")
        exit(1)
    
    main()

