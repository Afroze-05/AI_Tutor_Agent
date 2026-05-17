import sqlite3
import os

# Define the database path
DB_PATH = os.path.join(os.path.dirname(__file__), "conversations.db")

def init_db():
    """Initializes the database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            subject TEXT,
            user_message TEXT,
            ai_response TEXT,
            context_used TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_conversation(session_id, subject, user_message, ai_response, context_used=""):
    """Saves a single chat record to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversation_history (session_id, subject, user_message, ai_response, context_used)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, subject, user_message, ai_response, context_used))
    conn.commit()
    conn.close()

def get_conversations(session_id=None):
    """Retrieves conversation history, optionally filtered by session_id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if session_id:
        cursor.execute("SELECT * FROM conversation_history WHERE session_id = ? ORDER BY timestamp DESC", (session_id,))
    else:
        cursor.execute("SELECT * FROM conversation_history ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
