import sqlite3
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Ensure data directory exists
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "chat_history.db"


def get_db_connection():
    """Returns a connected SQLite database connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db():
    """Initialize the SQLite database schemas."""
    logger.info(f"Initializing SQLite database at {DB_PATH}")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL, -- 'user' or 'assistant'
            content TEXT NOT NULL,
            citations TEXT, -- JSON array of citation objects
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()
