import sqlite3
from typing import List, Optional
from aiogram import Bot

DB_FILE = "kinobot.db"

def initialize_database():
    """Initializes the database and creates tables if they don't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
            )
        """)
        # Create sponsors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sponsors (
                channel_id TEXT PRIMARY KEY
            )
        """)
        # Create videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_code TEXT PRIMARY KEY,
                message_id INTEGER NOT NULL
            )
        """)
        conn.commit()

# --- User Functions ---

def add_user(user_id: int):
    """Adds a new user to the database if they don't already exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def get_all_users() -> List[int]:
    """Retrieves a list of all user IDs from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]

# --- Sponsor Functions ---

def add_sponsor(channel_id: str):
    """Adds a new sponsor channel to the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO sponsors (channel_id) VALUES (?)", (channel_id,))
        conn.commit()

def remove_sponsor(channel_id: str) -> bool:
    """Removes a sponsor channel from the database. Returns True if successful."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sponsors WHERE channel_id = ?", (channel_id,))
        return cursor.rowcount > 0

def get_all_sponsors() -> List[str]:
    """Retrieves a list of all sponsor channel IDs from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM sponsors")
        return [row[0] for row in cursor.fetchall()]

# --- Video Functions ---

def add_video(video_code: str, message_id: int):
    """Adds or updates a video in the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO videos (video_code, message_id) VALUES (?, ?)", (video_code, message_id))
        conn.commit()

def get_video_message_id(video_code: str) -> Optional[int]:
    """Retrieves the message_id for a given video code."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message_id FROM videos WHERE video_code = ?", (video_code,))
        result = cursor.fetchone()
        return result[0] if result else None

# --- Subscription Check --- 

async def check_subscriptions(bot: Bot, user_id: int) -> bool:
    sponsors = get_all_sponsors()
    for channel in sponsors:
        if not channel.startswith('@') and not channel.startswith('-100'):
            channel = '@' + channel
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            return False
    return True
