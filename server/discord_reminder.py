import requests
import re
from datetime import datetime
from dateutil import parser
from dateutil.tz import UTC
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional

# Import Canvas functions
from canvas import get_assignments_next_week

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION - ADD TO YOUR .env FILE
# ============================================================================
# DISCORD_BOT_TOKEN=your_discord_bot_token
# DISCORD_USER_ID=your_discord_user_id
# CANVAS_API_KEY=your_canvas_api_key
# ============================================================================

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_USER_ID = os.getenv("DISCORD_USER_ID")


class DiscordBot:
    """Handles sending Direct Messages to Discord users via Bot API."""
    
    BASE_URL = "https://discord.com/api/v10"
    
    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Discord bot for DMs.
        
        Args:
            bot_token: Discord bot token
        """
        self.bot_token = bot_token or DISCORD_BOT_TOKEN
        
        if not self.bot_token:
            raise ValueError("DISCORD_BOT_TOKEN must be provided in .env file")
        
        self.headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://github.com/discord/discord-api-docs, 1.0)"
        }
        
        # Cache for DM channel IDs to avoid creating multiple channels
        self.dm_channels = {}
    
    def get_or_create_dm_channel(self, user_id: str) -> Optional[str]:
        """
        Get or create a DM channel with a user.
        Uses caching to avoid creating duplicate channels.
        
        Args:
            user_id: Discord user ID
        
        Returns:
            DM channel ID if successful, None otherwise
        """
        # Check cache first
        if user_id in self.dm_channels:
            return self.dm_channels[user_id]
        
        try:
            url = f"{self.BASE_URL}/users/@me/channels"
            # Discord API expects recipient_id as a string
            payload = {
                "recipient_id": str(user_id)
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            channel_data = response.json()
            channel_id = channel_data.get('id')
            
            if channel_id:
                # Cache the channel ID
                self.dm_channels[user_id] = channel_id
                print(f"Created DM channel {channel_id} with user {user_id}")
            
            return channel_id
            
        except requests.exceptions.HTTPError as e:
            error_msg = "Unknown error"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', str(e))
                    print(f"Discord API Error: {error_msg}")
                    print(f"Response: {e.response.text}")
                except:
                    error_msg = e.response.text
                    print(f"HTTP Error {e.response.status_code}: {error_msg}")
            else:
                print(f"HTTP Error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error creating DM channel: {e}")
            return None
    
    def send_dm(self, user_id: str, content: str = None, embed: Optional[Dict] = None) -> bool:
        """
        Send a direct message to a user.
        
        Args:
            user_id: Discord user ID
            content: Message content (optional if embed is provided)
            embed: Embed dictionary (optional)
        
        Returns:
            True if successful, False otherwise
        """
        # Get or create DM channel
        channel_id = self.get_or_create_dm_channel(user_id)
        if not channel_id:
            print(f"Failed to get/create DM channel with user {user_id}")
            return False
        
        # Prepare payload
        payload = {}
        if content:
            payload["content"] = content
        if embed:
            payload["embeds"] = [embed]
        
        if not payload:
            print("Error: Either content or embed must be provided")
            return False
        
        # Send message
        try:
            url = f"{self.BASE_URL}/channels/{channel_id}/messages"
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            print(f"Successfully sent DM to user {user_id}")
            return True
        except requests.exceptions.HTTPError as e:
            error_msg = "Unknown error"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', str(e))
                    print(f"Discord API Error sending DM: {error_msg}")
                    print(f"Response: {e.response.text}")
                except:
                    error_msg = e.response.text
                    print(f"HTTP Error {e.response.status_code}: {error_msg}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error sending DM: {e}")
            return False
    
    def send_dm_embed(self, user_id: str, title: str, description: str, 
                     color: int = 0x3498db, fields: Optional[List[Dict]] = None, 
                     footer: Optional[str] = None) -> bool:
        """
        Send an embedded DM to a user.
        
        Args:
            user_id: Discord user ID
            title: Embed title
            description: Embed description
            color: Embed color (hex as integer)
            fields: List of field dicts with 'name' and 'value' keys
            footer: Footer text
        
        Returns:
            True if successful, False otherwise
        """
        # Create embed with proper timestamp format
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),  # ISO 8601 with Z
        }
        
        if fields:
            embed["fields"] = fields
        
        if footer:
            embed["footer"] = {"text": footer}
        
        return self.send_dm(user_id, embed=embed)


class AssignmentReminderBot:
    """Main class that sends assignment reminders via Discord bot DMs."""
    
    def __init__(self, user_id: str):
        """
        Initialize reminder bot.
        
        Args:
            user_id: Discord user ID for DMs (required - must be provided)
        """
        if not user_id:
            raise ValueError("user_id must be provided as a parameter")
        
        self.user_id = str(user_id)  # Ensure it's a string
        self.bot = DiscordBot()
    
    def format_assignment_message(self, assignments: List[Dict]) -> str:
        """Format assignments into a readable message."""
        if not assignments:
            return "🎉 No assignments due in the next week!"
        
        message = "📚 **Upcoming Assignments (Next 7 Days)**\n\n"
        
        # Group by date
        by_date = {}
        for assignment in assignments:
            due_at = assignment.get('due_at')
            if due_at:
                try:
                    due_date = parser.parse(due_at)
                    if due_date.tzinfo:
                        due_date_utc = due_date.astimezone(UTC)
                    else:
                        due_date_utc = due_date.replace(tzinfo=UTC)
                    
                    date_key = due_date_utc.strftime("%Y-%m-%d")
                    if date_key not in by_date:
                        by_date[date_key] = []
                    by_date[date_key].append(assignment)
                except:
                    continue
        
        # Format by date
        for date_key in sorted(by_date.keys()):
            due_date = parser.parse(date_key)
            day_name = due_date.strftime("%A")
            date_str = due_date.strftime("%B %d, %Y")
            
            message += f"**📅 {day_name}, {date_str}**\n"
            
            for assignment in by_date[date_key]:
                name = assignment.get('name', 'Unnamed Assignment')
                course_name = assignment.get('course_name', assignment.get('course_id', 'Unknown Course'))
                due_at = assignment.get('due_at', '')
                
                # Format time
                time_str = ""
                if due_at:
                    try:
                        due_datetime = parser.parse(due_at)
                        if due_datetime.tzinfo:
                            due_datetime_utc = due_datetime.astimezone(UTC)
                        else:
                            due_datetime_utc = due_datetime.replace(tzinfo=UTC)
                        time_str = due_datetime_utc.strftime(" at %I:%M %p UTC")
                    except:
                        pass
                
                message += f"  • **{name}** ({course_name}){time_str}\n"
            
            message += "\n"
        
        return message
    
    def send_assignment_reminder(self) -> bool:
        """Fetch and send assignment reminders."""
        print("Fetching upcoming assignments...")
        # Use function from canvas.py
        assignments = get_assignments_next_week()
        
        print(f"Found {len(assignments)} assignments due in the next week")
        
        # Send as embed for better formatting
        fields = []
        if assignments:
            # Group by date for embed fields
            by_date = {}
            for assignment in assignments:
                due_at = assignment.get('due_at')
                if due_at:
                    try:
                        due_date = parser.parse(due_at)
                        if due_date.tzinfo:
                            due_date_utc = due_date.astimezone(UTC)
                        else:
                            due_date_utc = due_date.replace(tzinfo=UTC)
                        
                        date_key = due_date_utc.strftime("%Y-%m-%d")
                        if date_key not in by_date:
                            by_date[date_key] = []
                        by_date[date_key].append(assignment)
                    except:
                        continue
            
            for date_key in sorted(by_date.keys())[:10]:  # Limit to 10 fields (Discord limit)
                due_date = parser.parse(date_key)
                day_name = due_date.strftime("%A")
                date_str = due_date.strftime("%B %d")
                
                assignments_list = []
                for assignment in by_date[date_key]:
                    name = assignment.get('name', 'Unnamed')
                    course_name = assignment.get('course_name', assignment.get('course_id', 'Unknown'))
                    if len(name) > 40:
                        name = name[:37] + "..."
                    assignments_list.append(f"• {name} ({course_name})")
                
                field_value = "\n".join(assignments_list[:5])  # Limit per field
                if len(by_date[date_key]) > 5:
                    field_value += f"\n... and {len(by_date[date_key]) - 5} more"
                
                fields.append({
                    "name": f"{day_name}, {date_str}",
                    "value": field_value,
                    "inline": False
                })
        
        description = f"Found **{len(assignments)}** assignment(s) due in the next 7 days." if assignments else "🎉 No assignments due in the next week!"
        
        return self.bot.send_dm_embed(
            user_id=self.user_id,
            title="📚 Assignment Reminder",
            description=description,
            color=0xe74c3c if assignments else 0x2ecc71,  # Red if assignments, green if none
            fields=fields if fields else None,
            footer="Canvas Assignment Bot"
        )
    
    def send_individual_reminder(self, assignment: Dict, time_remaining: str) -> bool:
        """
        Send an individual reminder for a single assignment.
        
        Args:
            assignment: Assignment dictionary from Canvas API
            time_remaining: Human-readable string of time remaining (e.g., "1 hour", "45 minutes")
        
        Returns:
            True if successful, False otherwise
        """
        assignment_name = assignment.get('name', 'Unnamed Assignment')
        course_name = assignment.get('course_name', assignment.get('course_id', 'Unknown Course'))
        due_at = assignment.get('due_at', '')
        description = assignment.get('description', '')
        
        # Format due time
        due_time_str = "Unknown"
        if due_at:
            try:
                due_date = parser.parse(due_at)
                if due_date.tzinfo:
                    due_date_utc = due_date.astimezone(UTC)
                else:
                    due_date_utc = due_date.replace(tzinfo=UTC)
                
                # Format as readable date/time
                due_time_str = due_date_utc.strftime("%B %d at %I:%M %p UTC")
            except:
                due_time_str = due_at
        
        # Determine urgency color and emoji
        time_lower = time_remaining.lower()
        if 'hour' in time_lower:
            color = 0xf39c12  # Orange
            emoji = "⚠️"
        elif '30' in time_remaining or '45' in time_remaining:
            color = 0xe74c3c  # Red
            emoji = "🚨"
        else:  # 15 minutes or less
            color = 0xc0392b  # Dark red
            emoji = "🔥"
        
        # Create embed
        embed_description = f"**{assignment_name}** is due in **{time_remaining}**\n\n"
        embed_description += f"📚 **Course:** {course_name}\n"
        embed_description += f"⏰ **Due:** {due_time_str}\n"
        
        if description:
            # Clean HTML from description and truncate
            clean_description = re.sub('<[^<]+?>', '', description)
            if len(clean_description) > 200:
                clean_description = clean_description[:200] + "..."
            embed_description += f"\n📝 {clean_description}"
        
        return self.bot.send_dm_embed(
            user_id=self.user_id,
            title=f"{emoji} Assignment Due Soon",
            description=embed_description,
            color=color,
            footer=f"Canvas Assignment Reminder"
        )
    
    def send_study_session_reminder(self, session_name: str, date: str, time: str, location: str = "") -> bool:
        """Send a study session reminder."""
        message = f"📖 **Study Session Reminder**\n\n"
        message += f"**{session_name}**\n"
        message += f"📅 Date: {date}\n"
        message += f"⏰ Time: {time}\n"
        if location:
            message += f"📍 Location: {location}\n"
        
        return self.bot.send_dm(self.user_id, message)


def main():
    """Main function to test the bot."""
    import sys
    
    print("Discord Assignment Reminder Bot (DM Mode)")
    print("=" * 50)
    
    if not DISCORD_BOT_TOKEN:
        print("\n❌ ERROR: DISCORD_BOT_TOKEN not found in .env file!")
        print("\nPlease add the following to your .env file:")
        print("  DISCORD_BOT_TOKEN=your_bot_token")
        print("\nTo get your bot token:")
        print("  1. Go to https://discord.com/developers/applications")
        print("  2. Create a new application or select existing one")
        print("  3. Go to 'Bot' section and copy the token")
        return
    
    # Get user ID from command line argument or environment
    user_id = None
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    elif DISCORD_USER_ID:
        user_id = DISCORD_USER_ID
        print(f"Using user ID from .env file: {user_id}")
    
    if not user_id:
        print("\n❌ ERROR: Discord User ID not provided!")
        print("\nUsage: python discord_reminder.py <discord_user_id>")
        print("\nOr set DISCORD_USER_ID in .env file")
        print("\nTo get your user ID:")
        print("  1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)")
        print("  2. Right-click on your profile and select 'Copy User ID'")
        return
    
    try:
        bot = AssignmentReminderBot(user_id=user_id)
        print(f"\n✅ Bot initialized successfully!")
        print(f"📧 Will send DMs to user ID: {user_id}")
        print("\nSending assignment reminder...")
        
        success = bot.send_assignment_reminder()
        
        if success:
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message. Check your configuration and console logs.")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
