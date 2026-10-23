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
    
    # Watch history table with progress tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watch_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tmdb_id INTEGER UNIQUE,
        title TEXT,
        poster TEXT,
        year TEXT,
        rating REAL,
        media_type TEXT DEFAULT 'movie',
        progress_seconds REAL DEFAULT 0,
        duration_seconds REAL DEFAULT 0,
        last_watched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Video Catalogue Table (Step 3: Authorized video delivery)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS video_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tmdb_id INTEGER UNIQUE,
        title TEXT,
        playback_type TEXT DEFAULT 'hls', -- 'hls', 'mp4', 'cloudflare', 'embed'
        playback_url TEXT,
        is_available INTEGER DEFAULT 1,
        subtitles TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Check if progress_seconds exists in existing watch_history
    cursor.execute("PRAGMA table_info(watch_history)")
    columns = [col[1] for col in cursor.fetchall()]
    if "progress_seconds" not in columns:
        try:
            cursor.execute("ALTER TABLE watch_history ADD COLUMN progress_seconds REAL DEFAULT 0")
            cursor.execute("ALTER TABLE watch_history ADD COLUMN duration_seconds REAL DEFAULT 0")
        except Exception as e:
            pass
    
    # Seed high quality open test streams for initial verification
    seed_streams = [
        (19995, "Avatar", "hls", "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", 1),
        (233347, "Study Group", "hls", "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4", 1),
        (157336, "Interstellar", "hls", "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4", 1),
        (299536, "Avengers: Infinity War", "hls", "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", 1),
        (999001, "Big Buck Bunny (Official 1080p HLS)", "hls", "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", 1),
        (999002, "Sintel (4K Open Movie)", "mp4", "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4", 1),
        (999003, "Tears of Steel (Sci-Fi Film)", "mp4", "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4", 1),
        (999004, "Elephants Dream (Open Animation)", "mp4", "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4", 1)
    ]
    for tmdb_id, title, p_type, p_url, is_avail in seed_streams:
        cursor.execute("""
        INSERT OR IGNORE INTO video_catalog (tmdb_id, title, playback_type, playback_url, is_available)
        VALUES (?, ?, ?, ?, ?)
        """, (tmdb_id, title, p_type, p_url, is_avail))

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
    INSERT OR REPLACE INTO watch_history (tmdb_id, title, poster, year, rating, media_type, progress_seconds, duration_seconds, last_watched)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item.get("id") or item.get("tmdb_id"),
        item.get("title"),
        item.get("poster"),
        str(item.get("year", "2024")),
        float(item.get("rating", 7.5)),
        item.get("media_type", "movie"),
        float(item.get("progress_seconds", 0.0)),
        float(item.get("duration_seconds", 0.0)),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def update_playback_progress(tmdb_id, progress_seconds, duration_seconds):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM watch_history WHERE tmdb_id = ?", (tmdb_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("""
        UPDATE watch_history 
        SET progress_seconds = ?, duration_seconds = ?, last_watched = ?
        WHERE tmdb_id = ?
        """, (float(progress_seconds), float(duration_seconds), datetime.now().isoformat(), tmdb_id))
    else:
        cursor.execute("""
        INSERT INTO watch_history (tmdb_id, title, poster, year, rating, media_type, progress_seconds, duration_seconds, last_watched)
        VALUES (?, 'Watched Title', '', '2024', 7.5, 'movie', ?, ?, ?)
        """, (tmdb_id, float(progress_seconds), float(duration_seconds), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_video_stream(tmdb_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM video_catalog WHERE tmdb_id = ? AND is_available = 1", (tmdb_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def set_video_stream(tmdb_id, title, playback_type, playback_url, is_available=1, subtitles=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO video_catalog (tmdb_id, title, playback_type, playback_url, is_available, subtitles)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (tmdb_id, title, playback_type, playback_url, is_available, subtitles))
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
