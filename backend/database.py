import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Watchlist table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tmdb_id INTEGER UNIQUE,
        title TEXT,
        poster TEXT,
        year TEXT,
        rating REAL,
        media_type TEXT DEFAULT 'movie',
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Watch history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watch_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tmdb_id INTEGER UNIQUE,
        title TEXT,
        poster TEXT,
        year TEXT,
        rating REAL,
        media_type TEXT DEFAULT 'movie',
        last_watched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def add_to_watchlist(item):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO watchlist (tmdb_id, title, poster, year, rating, media_type, added_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        item.get("id") or item.get("tmdb_id"),
        item.get("title"),
        item.get("poster"),
        str(item.get("year", "2024")),
        float(item.get("rating", 7.5)),
        item.get("media_type", "movie"),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def remove_from_watchlist(tmdb_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE tmdb_id = ?", (tmdb_id,))
    conn.commit()
    conn.close()

def get_watchlist():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watchlist ORDER BY added_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_to_history(item):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO watch_history (tmdb_id, title, poster, year, rating, media_type, last_watched)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        item.get("id") or item.get("tmdb_id"),
        item.get("title"),
        item.get("poster"),
        str(item.get("year", "2024")),
        float(item.get("rating", 7.5)),
        item.get("media_type", "movie"),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_history(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watch_history ORDER BY last_watched DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def clear_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watch_history")
    conn.commit()
    conn.close()

# Auto-init on load
init_db()
