# Discord Bot Setup for Direct Messages

This guide explains how to set up a Discord bot to send direct messages (DMs) to users.

## Important: Webhooks vs Bot

- **Webhooks**: Can only send messages to channels, NOT direct messages
- **Bot**: Can send direct messages to users, but requires more setup

## Setup Steps

### 1. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot" and confirm
5. Under "Token", click "Reset Token" or "Copy" to get your bot token
6. **Save this token** - you'll need it for `DISCORD_BOT_TOKEN`

### 2. Get Your User ID

To receive DMs, the bot needs your Discord User ID:

1. Enable Developer Mode in Discord:
   - User Settings → Advanced → Enable "Developer Mode"
2. Get your User ID:
   - Right-click on your profile (or any user)
   - Click "Copy User ID"
   - **Save this ID** - you'll need it for `DISCORD_USER_ID`

### 3. Bot Permissions

The bot needs the following permissions:
- Send Messages
- Embed Links
- Read Message History

### 4. Invite Bot to Server (Optional but Recommended)

Even for DMs, it's recommended to add the bot to a server:

1. In Developer Portal, go to "OAuth2" → "URL Generator"
2. Select scopes: `bot`
3. Select permissions: `Send Messages`, `Embed Links`, `Read Message History`
4. Copy the generated URL and open it in your browser
5. Select a server and authorize the bot

### 5. Enable DMs

**Important**: For the bot to DM you:
- You must have DMs enabled from server members
- The bot must be in at least one server with you (or you must have shared a server)
- Discord has rate limits on DM creation

### 6. Environment Variables

Add these to your `.env` file:

```env
# For Direct Messages (Bot Mode)
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_USER_ID=your_discord_user_id_here

# For Channel Messages (Webhook Mode - optional, use if you want channel messages)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN

# Canvas API
CANVAS_API_KEY=your_canvas_api_key
```

## Usage

### Mode Selection

The bot automatically detects which mode to use:

- **DM Mode**: If `DISCORD_BOT_TOKEN` and `DISCORD_USER_ID` are set
- **Webhook Mode**: If `DISCORD_WEBHOOK_URL` is set (and DM mode is not configured)

### In Code

```python
from discord_reminder import AssignmentReminderBot

# DM Mode (automatically selected if bot token and user ID are set)
bot = AssignmentReminderBot(use_dm=True, user_id="123456789012345678")

# Webhook Mode (for channel messages)
bot = AssignmentReminderBot(use_dm=False)
```

### Update Reminder Service

The reminder service will automatically use DM mode if configured:

```python
# In reminder_service.py, the bot is initialized automatically
# It will use DM mode if DISCORD_BOT_TOKEN and DISCORD_USER_ID are set
```

## Troubleshooting

### "Failed to create DM channel"

**Possible causes:**
1. User ID is incorrect
2. Bot is not in any server with the user
3. User has DMs disabled from server members
4. Bot token is invalid

**Solutions:**
1. Verify your user ID is correct (enable Developer Mode and copy it again)
2. Add the bot to a server and ensure you're also in that server
3. Check Discord settings: User Settings → Privacy & Safety → Allow direct messages from server members
4. Verify bot token is correct in Developer Portal

### "Invalid bot token"

**Solution:**
1. Go to Discord Developer Portal
2. Reset the bot token
3. Update `DISCORD_BOT_TOKEN` in your `.env` file

### "Rate Limited"

Discord has rate limits on creating DM channels. If you're sending many reminders:
- The bot will handle rate limits automatically
- Consider using webhook mode for bulk messages
- DM mode is better for individual personalized reminders

## Security Notes

- **Never commit your bot token or user ID to version control**
- Keep your `.env` file in `.gitignore`
- Bot tokens can be reset in the Developer Portal if compromised
- User IDs are not sensitive but should still be kept private

## Example .env File

```env
# Discord Bot (for DMs)
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_USER_ID=your_discord_user_id_here

# Discord Webhook (for channel messages - optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN

# Canvas API
CANVAS_API_KEY=your_canvas_api_key_here
```

## Testing

Test your bot setup:

```bash
# Test DM mode
python discord_reminder.py

# Or test via Flask endpoint
curl http://127.0.0.1:5000/reminders/test-now
```

## Support

If you encounter issues:
1. Check the console logs for detailed error messages
2. Verify all environment variables are set correctly
3. Test the bot token by sending a message in a server channel first
4. Ensure the bot has the correct permissions

