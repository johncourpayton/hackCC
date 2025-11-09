# Discord Webhook Setup Guide

This guide will help you set up Discord webhooks to send assignment reminders and study session notifications.

## Required Keys and Tokens

You'll need to add the following to your `.env` file in the `server/` directory:

### Discord Webhook URL

1. **Get Discord Webhook URL:**
   - Open Discord and go to your server
   - Right-click on the channel where you want to receive reminders
   - Click "Edit Channel" → "Integrations" → "Webhooks"
   - Click "New Webhook" or "Create Webhook"
   - Give it a name (e.g., "Canvas Bot")
   - Click "Copy Webhook URL"
   - Add to `.env`:
     ```
     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
     ```

### Canvas API (Already Configured)

Your Canvas API key should already be in `.env`:
```
CANVAS_API_KEY=your_canvas_api_key
```

## Complete .env File Example

```env
# Canvas API
CANVAS_API_KEY=your_canvas_api_key_here

# Discord Webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyz
```

## Installation

1. Install required packages:
   ```bash
   pip install requests python-dateutil python-dotenv
   ```

2. Test the bot:
   ```bash
   python discord_reminder.py
   ```

## Usage

### Send Assignment Reminders

```python
from discord_reminder import AssignmentReminderBot

bot = AssignmentReminderBot()
bot.send_assignment_reminder()
```

### Send Study Session Reminder

```python
bot.send_study_session_reminder(
    session_name="Physics Lab Review",
    date="Monday, January 15, 2024",
    time="2:00 PM",
    location="Library Room 201"
)
```

### Schedule Automatic Reminders

Use the `scheduler.py` script to run reminders automatically:

```bash
python scheduler.py
```

Or set up a cron job / Windows Task Scheduler to run it daily.

## Troubleshooting

### "DISCORD_WEBHOOK_URL not found"
- Make sure you've added `DISCORD_WEBHOOK_URL` to your `.env` file
- Verify the webhook URL is correct and complete

### "Failed to send message"
- Check that your webhook URL is correct
- Verify the webhook is still active in Discord
- Make sure the webhook has permission to send messages in the channel
- Check that the webhook hasn't been deleted

### "CANVAS_API_KEY not found"
- Add your Canvas API key to the `.env` file

### Webhook Not Working?
- Make sure the webhook URL is complete and includes both the ID and token
- Verify the webhook is enabled in Discord channel settings
- Check that you have "Manage Webhooks" permission in the server

