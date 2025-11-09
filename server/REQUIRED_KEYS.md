# Required Environment Variables

This document lists all required and optional environment variables for the reminder system.

## Required Variables

### Canvas API
- **`CANVAS_API_KEY`** (Required)
  - Your Canvas LMS API access token
  - Get it from: Canvas → Account → Settings → New Access Token
  - Format: `2352~...`

### Discord Bot

- **`DISCORD_BOT_TOKEN`** (Required)
  - Your Discord bot token
  - Get it from: [Discord Developer Portal](https://discord.com/developers/applications)
  - Format: `MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.AbCdEf.GhIjKlMnOpQr...`

## Optional Variables

### Discord User ID (For Scheduler)

- **`DISCORD_USER_ID`** (Optional)
  - Discord user ID for scheduled reminders
  - Can be set in `.env` file OR via API endpoint `/reminders/set-user`
  - If not set, scheduler will skip reminder checks
  - Get it by: Enabling Developer Mode → Right-click profile → "Copy User ID"
  - Format: `123456789012345678` (numeric string)

## Important: User ID is Now a Parameter

**The Discord User ID is now supplied as a parameter, not from `.env` file.**

### For API Endpoints
All reminder endpoints require `user_id` in the JSON request body (POST requests):
- `POST /reminders/test` with body: `{"user_id": "123456789012345678"}`
- `POST /reminders/test-now` with body: `{"user_id": "123456789012345678"}`
- `POST /reminders/force-check` with body: `{"user_id": "123456789012345678"}`
- `POST /reminders/set-user` with body: `{"user_id": "123456789012345678"}`

See `API_ENDPOINTS.md` for complete API documentation with examples.

### For Scheduled Reminders
The scheduler can use `DISCORD_USER_ID` from `.env` OR you can set it via API:
- POST `/reminders/set-user` with body: `{"user_id": "123456789012345678"}`

### For Command Line
```bash
python discord_reminder.py <discord_user_id>
```

## Example .env File

```env
# Canvas API (Required)
CANVAS_API_KEY=your_canvas_token_here

# Discord Bot Token (Required)
DISCORD_BOT_TOKEN=your_bot_token_here

# Discord User ID (Optional - for scheduler)
DISCORD_USER_ID=your_discord_user_id_here
```

## Setup Guides

- **Discord Bot Setup**: See `DISCORD_BOT_SETUP.md`
- **Canvas API Setup**: See Canvas documentation

## Security Notes

⚠️ **Never commit these values to version control!**

- Keep your `.env` file in `.gitignore`
- Bot tokens and API keys are sensitive
- User IDs are less sensitive but should still be kept private
- If a token is compromised, regenerate it immediately

## Verification

To verify your configuration:

1. Check that `.env` file exists in the `server/` directory
2. Test with command line: `python discord_reminder.py <user_id>`
3. Test via API: POST request with JSON body (see examples below)
4. Check console for initialization messages
5. Use debug endpoint: `GET http://127.0.0.1:5000/reminders/debug?user_id=<user_id>` or POST with JSON body

## Usage Examples

### Command Line
```bash
# Test with specific user ID
python discord_reminder.py 123456789012345678
```

### API Endpoints (POST with JSON body)
```bash
# Test immediate reminder
curl -X POST "http://127.0.0.1:5000/reminders/test-now" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123456789012345678"}'

# Set user for scheduled reminders
curl -X POST "http://127.0.0.1:5000/reminders/set-user" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123456789012345678"}'

# Force check reminders
curl -X POST "http://127.0.0.1:5000/reminders/force-check" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123456789012345678"}'

# Test reminder system
curl -X POST "http://127.0.0.1:5000/reminders/test" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123456789012345678"}'
```

### Frontend JavaScript Example
```javascript
// Send test reminder
fetch('http://127.0.0.1:5000/reminders/test-now', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_id: '123456789012345678'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

See `API_ENDPOINTS.md` for complete API documentation.

## Troubleshooting

### "user_id must be provided"
- Provide user_id in JSON request body for POST endpoints
- Or set DISCORD_USER_ID in .env for scheduler
- Or use `/reminders/set-user` endpoint to configure scheduler
- See `API_ENDPOINTS.md` for complete API documentation

### "DISCORD_BOT_TOKEN must be provided"
- Set `DISCORD_BOT_TOKEN` in your `.env` file
- Get token from Discord Developer Portal

### Bot not sending DMs
- Verify bot token is correct
- Ensure bot is in at least one server with the user
- Check that DMs are enabled from server members
- Verify user ID is correct (must be numeric string)
- Check console logs for detailed error messages

### "Failed to create DM channel"
- Bot must be in at least one server with the user
- User must have DMs enabled from server members
- Verify user ID is correct
- Check bot permissions in Discord Developer Portal

### Scheduler not running
- Set `DISCORD_USER_ID` in `.env` file, OR
- Use POST `/reminders/set-user` endpoint to configure it
- Check scheduler status: `http://127.0.0.1:5000/reminders/status`
