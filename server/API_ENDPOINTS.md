# API Endpoints Documentation

This document describes all API endpoints for the reminder system.

## Base URL

All endpoints are relative to: `http://127.0.0.1:5000`

## Endpoints

### 1. Test Immediate Reminder

Send a test reminder immediately to verify Discord bot is working.

**Endpoint:** `POST /reminders/test-now`

**Request Body:**
```json
{
  "user_id": "123456789012345678"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Test reminder sent immediately to Discord! Check your DMs.",
  "user_id": "123456789012345678",
  "test_assignment": {
    "name": "🧪 TEST Assignment - Please Ignore",
    "due_in": "1 minute"
  }
}
```

**Example (JavaScript):**
```javascript
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

---

### 2. Test Reminder System

Test the full reminder system with a test assignment due in 14 minutes.

**Endpoint:** `POST /reminders/test`

**Request Body:**
```json
{
  "user_id": "123456789012345678"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Test reminder check completed. Check console for debug output and Discord for reminders.",
  "user_id": "123456789012345678",
  "test_assignment_due_in": "14 minutes",
  "note": "The 15-minute reminder should have been sent (it's 1 minute past the 15-minute mark)"
}
```

**Example (JavaScript):**
```javascript
fetch('http://127.0.0.1:5000/reminders/test', {
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

---

### 3. Force Check Reminders

Manually trigger a reminder check for all upcoming assignments.

**Endpoint:** `POST /reminders/force-check`

**Request Body:**
```json
{
  "user_id": "123456789012345678"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Reminder check completed. Check console for output.",
  "user_id": "123456789012345678",
  "time": "2024-01-15T14:30:00.000Z"
}
```

**Example (JavaScript):**
```javascript
fetch('http://127.0.0.1:5000/reminders/force-check', {
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

---

### 4. Set Scheduled User

Configure which user ID should receive scheduled reminders (runs every minute).

**Endpoint:** `POST /reminders/set-user`

**Request Body:**
```json
{
  "user_id": "123456789012345678"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Scheduled user ID set to 123456789012345678",
  "user_id": "123456789012345678",
  "note": "Scheduler will now send reminders to this user"
}
```

**Example (JavaScript):**
```javascript
fetch('http://127.0.0.1:5000/reminders/set-user', {
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

---

### 5. Debug Status

Check system status and optionally test DM sending.

**Endpoint:** `GET /reminders/debug` or `POST /reminders/debug`

**GET Request (Query Parameter):**
```
GET /reminders/debug?user_id=123456789012345678
```

**POST Request (JSON Body):**
```json
{
  "user_id": "123456789012345678"
}
```

**Response:**
```json
{
  "mode": "DM (Bot)",
  "discord_bot_token_set": true,
  "scheduled_user_id": "123456789012345678",
  "test_user_id": "123456789012345678",
  "tracker_file_exists": true,
  "scheduler_running": true,
  "current_time_utc": "2024-01-15T14:30:00.000Z",
  "test_message_sent": true
}
```

**Example (JavaScript - GET):**
```javascript
fetch('http://127.0.0.1:5000/reminders/debug?user_id=123456789012345678')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Example (JavaScript - POST):**
```javascript
fetch('http://127.0.0.1:5000/reminders/debug', {
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

---

### 6. Health Check

Check if the server and scheduler are running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "scheduler_running": true
}
```

**Example (JavaScript):**
```javascript
fetch('http://127.0.0.1:5000/health')
  .then(response => response.json())
  .then(data => console.log(data));
```

---

### 7. Reminders Status

Get status of the reminder system and scheduler.

**Endpoint:** `GET /reminders/status`

**Response:**
```json
{
  "scheduler_running": true,
  "jobs": ["check_reminders"]
}
```

**Example (JavaScript):**
```javascript
fetch('http://127.0.0.1:5000/reminders/status')
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## Error Responses

All endpoints may return error responses with the following format:

```json
{
  "status": "error",
  "message": "Error description",
  "error_type": "ValueError"
}
```

Common error codes:
- `400` - Bad Request (missing or invalid parameters)
- `500` - Internal Server Error

## Frontend Integration Example

### React/TypeScript Example

```typescript
const API_BASE_URL = 'http://127.0.0.1:5000';

interface ReminderRequest {
  user_id: string;
}

async function sendTestReminder(userId: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/reminders/test-now`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId } as ReminderRequest),
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      console.log('Reminder sent successfully!');
    } else {
      console.error('Error:', data.message);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
}

// Usage
sendTestReminder('123456789012345678');
```

### Axios Example

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Send test reminder
async function sendTestReminder(userId) {
  try {
    const response = await api.post('/reminders/test-now', {
      user_id: userId
    });
    console.log('Success:', response.data);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// Set scheduled user
async function setScheduledUser(userId) {
  try {
    const response = await api.post('/reminders/set-user', {
      user_id: userId
    });
    console.log('Success:', response.data);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}
```

## CORS (Cross-Origin Resource Sharing)

If your frontend is on a different origin (different port/domain), you may need to enable CORS in Flask. Add this to `app.py`:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

Then install: `pip install flask-cors`

## Notes

- All user IDs must be strings (numeric strings)
- All POST requests require `Content-Type: application/json` header
- The scheduler runs automatically every 60 seconds if a user ID is configured
- User IDs can be set via `.env` file (`DISCORD_USER_ID`) or via the `/reminders/set-user` endpoint

