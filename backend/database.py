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
    
    # Watchlist table with user_id and index
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default_user',
        tmdb_id INTEGER,
        title TEXT,
        poster TEXT,
        year TEXT,
        rating REAL,
        media_type TEXT DEFAULT 'movie',
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, tmdb_id)
    )
    """)
    
    # Watch history table with episode/season tracking and compound user index
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watch_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default_user',
        tmdb_id INTEGER,
        season INTEGER DEFAULT 1,
        episode INTEGER DEFAULT 1,
        title TEXT,
        poster TEXT,
        year TEXT,
        rating REAL,
        media_type TEXT DEFAULT 'movie',
        progress_seconds REAL DEFAULT 0,
        duration_seconds REAL DEFAULT 0,
        last_watched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, tmdb_id, season, episode)
    )
    """)

    # Video Catalogue Table (Authorized video delivery)
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

    # Migration check for existing databases (adds missing columns if upgrading)
    cursor.execute("PRAGMA table_info(watch_history)")
    columns = [col[1] for col in cursor.fetchall()]
    if "season" not in columns:
        try:
            cursor.execute("ALTER TABLE watch_history ADD COLUMN season INTEGER DEFAULT 1")
            cursor.execute("ALTER TABLE watch_history ADD COLUMN episode INTEGER DEFAULT 1")
            cursor.execute("ALTER TABLE watch_history ADD COLUMN user_id TEXT DEFAULT 'default_user'")
        except Exception:
            pass

    cursor.execute("PRAGMA table_info(watchlist)")
    wl_columns = [col[1] for col in cursor.fetchall()]
    if "user_id" not in wl_columns:
        try:
            cursor.execute("ALTER TABLE watchlist ADD COLUMN user_id TEXT DEFAULT 'default_user'")
        except Exception:
            pass

    # Performance Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id, added_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON watch_history(user_id, last_watched DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_catalog_tmdb ON video_catalog(tmdb_id)")
    
    conn.commit()
    conn.close()

def add_to_watchlist(item, user_id="default_user"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO watchlist (user_id, tmdb_id, title, poster, year, rating, media_type, added_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
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

def remove_from_watchlist(tmdb_id, user_id="default_user"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE tmdb_id = ? AND user_id = ?", (tmdb_id, user_id))
    conn.commit()
    conn.close()

def get_watchlist(user_id="default_user"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watchlist WHERE user_id = ? ORDER BY added_at DESC", (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_to_history(item, user_id="default_user"):
    conn = get_connection()
    cursor = conn.cursor()
    s = int(item.get("season", 1))
    e = int(item.get("episode", 1))
    cursor.execute("""
    INSERT OR REPLACE INTO watch_history (user_id, tmdb_id, season, episode, title, poster, year, rating, media_type, progress_seconds, duration_seconds, last_watched)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        item.get("id") or item.get("tmdb_id"),
        s,
        e,
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

def update_playback_progress(tmdb_id, progress_seconds, duration_seconds, user_id="default_user", season=1, episode=1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, title, poster, year, rating, media_type FROM watch_history 
    WHERE user_id = ? AND tmdb_id = ? AND season = ? AND episode = ?
    """, (user_id, tmdb_id, season, episode))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("""
        UPDATE watch_history 
        SET progress_seconds = ?, duration_seconds = ?, last_watched = ?
        WHERE id = ?
        """, (float(progress_seconds), float(duration_seconds), datetime.now().isoformat(), row["id"]))
    else:
        # Check if title metadata exists from any previous watch of this title
        cursor.execute("SELECT title, poster, year, rating, media_type FROM watch_history WHERE tmdb_id = ? LIMIT 1", (tmdb_id,))
        meta = cursor.fetchone()
        t = meta["title"] if meta else "Watched Title"
        p = meta["poster"] if meta else ""
        y = meta["year"] if meta else "2024"
        r = meta["rating"] if meta else 7.5
        m = meta["media_type"] if meta else ("tv" if season > 1 or episode > 1 else "movie")
        
        cursor.execute("""
        INSERT INTO watch_history (user_id, tmdb_id, season, episode, title, poster, year, rating, media_type, progress_seconds, duration_seconds, last_watched)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, tmdb_id, season, episode, t, p, y, r, m, float(progress_seconds), float(duration_seconds), datetime.now().isoformat()))
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

def get_history(limit=20, user_id="default_user"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watch_history WHERE user_id = ? ORDER BY last_watched DESC LIMIT ?", (user_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def clear_history(user_id="default_user"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watch_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Auto-init on load
init_db()
