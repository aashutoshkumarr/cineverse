import os
import sys
import json
import re
from urllib.parse import urlparse
from fastapi import FastAPI, Query, HTTPException, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

import api_service as api
from backend import database as db
from backend import recommender as rec
from backend import streaming_service as stream

app = FastAPI(title="Cineverse API", version="2.0.0")

# ---------------------------------------------------------
# Secure CORS Configuration
# Production-ready: Allows localhost dev ports and custom origins via env
# Supports regex matching for local preview ports (3000-3005, 5173, etc.)
# ---------------------------------------------------------
custom_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins_list = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
]
if custom_origins:
    for origin in custom_origins.split(","):
        o = origin.strip()
        if o and o not in allowed_origins_list:
            allowed_origins_list.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?",
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Load catalog once at startup
CATALOG_PATH = os.path.join(BASE_DIR, "netmirror_catalog.json")
CATALOG = []
try:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        CATALOG = json.load(f)
    print(f"Loaded {len(CATALOG)} movies in FastAPI!")
except Exception as e:
    print("Catalog load error:", e)

class WatchItem(BaseModel):
    id: Optional[int] = None
    tmdb_id: Optional[int] = None
    title: str
    poster: Optional[str] = None
    year: Optional[str] = "2024"
    rating: Optional[float] = 7.5
    media_type: Optional[str] = "movie"

class ProgressUpdate(BaseModel):
    progress_seconds: float
    duration_seconds: float
    season: Optional[int] = 1
    episode: Optional[int] = 1

class CustomStreamInput(BaseModel):
    tmdb_id: int
    title: str
    playback_type: str = "hls"
    playback_url: str
    subtitles: Optional[str] = None

@app.get("/")
def root():
    return {
        "app": "Cineverse API",
        "status": "running",
        "frontend_url": "http://localhost:3001",
        "docs_url": "http://127.0.0.1:8000/docs",
        "catalog_size": len(CATALOG)
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "total_catalog": len(CATALOG)}

@app.get("/api/movies")
def get_movies(
    page: int = Query(1, ge=1, description="Page number (positive integer)"),
    limit: int = Query(24, ge=1, le=100, description="Items per page (max 100)"),
    country: Optional[str] = "All",
    category: Optional[str] = "All",
    language: Optional[str] = "All"
):
    results = CATALOG
    if country and country != "All":
        results = [m for m in results if m.get("country") == country]
    if category and category != "All":
        results = [m for m in results if m.get("category") == category]
    if language and language != "All":
        results = [m for m in results if language in m.get("languages", [m.get("language")])]
        
    total_items = len(results)
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, total_items)
    
    return {
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": max(1, (total_items + limit - 1) // limit),
        "results": results[start_idx:end_idx]
    }

@app.get("/api/shelves")
def get_shelves():
    """Returns curated shelves for the Netflix/NetMirror home view with ML & Resume integration."""
    def take(items, n=10):
        return items[:n]

    shelves = []

    # 1. Continue Watching Shelf (if user has watch history with progress)
    history = db.get_history(10)
    continue_watching = [
        {
            **h,
            "id": h["tmdb_id"],
            "progress_percent": round((h.get("progress_seconds", 0) / max(h.get("duration_seconds", 1), 1)) * 100, 1)
        }
        for h in history if h.get("progress_seconds", 0) > 0
    ]
    if continue_watching:
        shelves.append({
            "id": "continue_watching",
            "title": "▶ Continue Watching",
            "tag": "Resume Playback",
            "is_continue_watching": True,
            "items": continue_watching
        })

    # 2. Because You Watched ... (ML Recommender Integration)
    if history:
        last_watched = history[0]
        recs = rec.get_ml_recommendations(last_watched.get("tmdb_id"), last_watched.get("title"), limit=10)
        if recs:
            shelves.append({
                "id": "because_you_watched",
                "title": f"🤖 Because You Watched {last_watched.get('title')}",
                "tag": "AI Recommender",
                "items": recs
            })

    # Curate high-impact trending blockbusters for Trending Now
    priority_ids = [385687, 200709, 132117, 19995, 157336, 27205, 99966, 550, 507941, 320873] # Fast X, Weak Hero, Farzi, Avatar, Interstellar, Inception, All of Us Are Dead, Fight Club, Section 375, Dhanak
    priority_items = [m for pid in priority_ids for m in CATALOG if m.get("id") == pid]
    other_items = [m for m in CATALOG if m.get("id") not in priority_ids and float(m.get("rating", 0)) >= 7.8]
    trending_items = (priority_items + other_items)[:12]

    # Trending Now
    shelves.append({"id": "trending", "title": "🔥 Trending Now on Cineverse", "tag": "Popular Blockbusters", "items": trending_items})
    
    # Curated categories
    cartoons = [m for m in CATALOG if m.get("category") == "Animation"]
    anime = [m for m in CATALOG if m.get("category") == "Anime"]
    
    kdrama_priority = [93405, 200709, 99966, 117376, 127529, 215072, 96648, 113268, 233347]
    kdrama_favs = [m for kid in kdrama_priority for m in CATALOG if m.get("id") == kid]
    kdrama_others = [m for m in CATALOG if m.get("country") == "Korea" and m.get("id") not in kdrama_priority and "reality" not in [g.lower() for g in m.get("genres", [])] and m.get("title") != "Infinite Challenge"]
    kdrama = kdrama_favs + kdrama_others

    hindi = [m for m in CATALOG if m.get("country") == "India" and m.get("category") == "Hindi"]
    south = [m for m in CATALOG if m.get("country") == "India" and m.get("category") in ["Telugu", "Tamil", "Malayalam"]]
    hollywood = [m for m in CATALOG if m.get("country") == "USA" and m.get("category") == "Hollywood"]
    hall_of_fame = [m for m in CATALOG if float(m.get("rating", 0)) >= 8.2]
    china = [m for m in CATALOG if m.get("country") == "China"]
    uk = [m for m in CATALOG if m.get("country") == "UK"]
    bangla = [m for m in CATALOG if m.get("country") == "Bangladesh"]

    shelves.extend([
        {"id": "cartoons", "title": "🧸 Cartoons & Nostalgia (Doraemon, Shin-chan, Bheem, Tom & Jerry)", "tag": "Cartoons", "items": take(cartoons, 10)},
        {"id": "anime", "title": "⚔️ Top Anime & Japanese Animation", "tag": "AniList Live", "items": take(anime, 10)},
        {"id": "kdrama", "title": "🇰🇷 Top K-Dramas & Korean Cinema", "tag": "K-Drama", "items": take(kdrama, 10)},
        {"id": "hindi", "title": "🇮🇳 Bollywood & Hindi Cinema Blockbusters", "tag": "Bollywood", "items": take(hindi, 10)},
        {"id": "south", "title": "🏹 South Indian Pan-India Action (Tollywood, Kollywood, Mollywood)", "tag": "South Action", "items": take(south, 10)},
        {"id": "hollywood", "title": "🇺🇸 Hollywood & Western Blockbusters", "tag": "Hollywood", "items": take(hollywood, 10)},
        {"id": "hall_of_fame", "title": "⭐ Hall of Fame: All-Time Masterpieces (Rating 8.2+)", "tag": "IMDb / TMDB Gold", "items": take(hall_of_fame, 10)},
        {"id": "china", "title": "🇨🇳 Chinese Cinema & C-Dramas", "tag": "C-Drama", "items": take(china, 10)},
        {"id": "uk", "title": "🇬🇧 British Classics & Crime Series", "tag": "BBC & UK", "items": take(uk, 10)},
        {"id": "bangla", "title": "🇧🇩 Bangladeshi Cinema & Hits", "tag": "Bengali Cinema", "items": take(bangla, 10)}
    ])

    return shelves

@app.get("/api/search")
def search(q: str = Query(..., min_length=1)):
    clean_q = q.strip().lower()
    # 1. Search local catalog first (instantaneous)
    local_matches = [m for m in CATALOG if clean_q in m.get("clean_title", "").lower() or clean_q in m.get("title", "").lower()]
    
    # 2. Also search live TMDB multi-search
    tmdb_matches = api.search_tmdb_multi(q)
    
    # Merge uniquely
    merged = []
    seen = set()
    for m in local_matches:
        merged.append(m)
        seen.add(m.get("title", "").lower())
        
    for m in tmdb_matches:
        if m.get("title", "").lower() not in seen:
            seen.add(m.get("title", "").lower())
            merged.append(m)
            
    return {"query": q, "count": len(merged), "results": merged[:30]}

import requests
import time
from datetime import datetime

# Bounded In-Memory Cache with TTL & Max Capacity to prevent memory leaks
class BoundedTTLCache:
    def __init__(self, maxsize=500, ttl_seconds=3600):
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self._cache = {}

    def get(self, key):
        if key in self._cache:
            val, expire_at = self._cache[key]
            if time.time() < expire_at:
                return val
            del self._cache[key]
        return None

    def set(self, key, value):
        if len(self._cache) >= self.maxsize:
            # Drop oldest 20% entries
            oldest_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])[:int(self.maxsize * 0.2)]
            for k in oldest_keys:
                self._cache.pop(k, None)
        self._cache[key] = (value, time.time() + self.ttl)

    def __contains__(self, key):
        return self.get(key) is not None

    def __getitem__(self, key):
        v = self.get(key)
        if v is None:
            raise KeyError(key)
        return v

    def __setitem__(self, key, value):
        self.set(key, value)

_extended_cache = BoundedTTLCache(maxsize=1000, ttl_seconds=7200)
headers_tmdb = api.get_tmdb_headers()

def format_release_date(date_str):
    if not date_str:
        return "2024"
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return date_str

import urllib.parse

_KNOWN_SEASONS = {
    # Korean Mega-Hits
    93405: [{"season": 1, "episodes": 9, "name": "Season 1"}, {"season": 2, "episodes": 6, "name": "Season 2"}], # Squid Game
    200709: [{"season": 1, "episodes": 8, "name": "Season 1"}, {"season": 2, "episodes": 8, "name": "Season 2"}], # Weak Hero Class 1
    200710: [{"season": 1, "episodes": 8, "name": "Season 1"}], # Weak Hero [English Dub]
    200711: [{"season": 1, "episodes": 8, "name": "Season 1"}], # Weak Hero Class 1 [Korea]
    99966: [{"season": 1, "episodes": 12, "name": "Season 1"}], # All of Us Are Dead
    117376: [{"season": 1, "episodes": 20, "name": "Season 1"}], # Vincenzo
    127529: [{"season": 1, "episodes": 8, "name": "Season 1"}], # Bloodhounds
    215072: [{"season": 1, "episodes": 8, "name": "Season 1"}], # A Shop for Killers
    96648: [{"season": 1, "episodes": 10, "name": "Season 1"}, {"season": 2, "episodes": 8, "name": "Season 2"}, {"season": 3, "episodes": 8, "name": "Season 3"}], # Sweet Home
    113268: [{"season": 1, "episodes": 16, "name": "Season 1"}, {"season": 2, "episodes": 12, "name": "Season 2"}], # The Uncanny Counter
    233347: [{"season": 1, "episodes": 10, "name": "Season 1"}], # Study Group
    216390: [{"season": 1, "episodes": 8, "name": "Season 1"}], # Death's Game
    213713: [{"season": 1, "episodes": 16, "name": "Season 1"}], # My Demon
    94796: [{"season": 1, "episodes": 16, "name": "Season 1"}], # Crash Landing on You
    136283: [{"season": 1, "episodes": 16, "name": "Season 1"}], # The Glory
    5092: [{"season": 1, "episodes": 24, "name": "Season 1"}, {"season": 2, "episodes": 24, "name": "Season 2"}, {"season": 3, "episodes": 24, "name": "Season 3"}], # Infinite Challenge

    # Indian Mega-Hits
    132117: [{"season": 1, "episodes": 8, "name": "Season 1"}], # Farzi
    86847: [{"season": 1, "episodes": 9, "name": "Season 1"}, {"season": 2, "episodes": 10, "name": "Season 2"}, {"season": 3, "episodes": 10, "name": "Season 3"}], # Mirzapur
    100757: [{"season": 1, "episodes": 8, "name": "Season 1"}, {"season": 2, "episodes": 8, "name": "Season 2"}, {"season": 3, "episodes": 8, "name": "Season 3"}], # Panchayat
    93425: [{"season": 1, "episodes": 10, "name": "Season 1"}, {"season": 2, "episodes": 9, "name": "Season 2"}], # The Family Man
    79244: [{"season": 1, "episodes": 8, "name": "Season 1"}, {"season": 2, "episodes": 8, "name": "Season 2"}], # Sacred Games
    100128: [{"season": 1, "episodes": 8, "name": "Season 1"}, {"season": 2, "episodes": 8, "name": "Season 2"}], # Asur
    110912: [{"season": 1, "episodes": 10, "name": "Season 1"}], # Scam 1992
    102714: [{"season": 1, "episodes": 9, "name": "Season 1"}], # Paatal Lok

    # Hollywood Mega-Hits
    66732: [{"season": 1, "episodes": 8, "name": "Season 1"}, {"season": 2, "episodes": 9, "name": "Season 2"}, {"season": 3, "episodes": 8, "name": "Season 3"}, {"season": 4, "episodes": 9, "name": "Season 4"}], # Stranger Things
    76479: [{"season": 1, "episodes": 8, "name": "Season 1"}, {"season": 2, "episodes": 8, "name": "Season 2"}, {"season": 3, "episodes": 8, "name": "Season 3"}, {"season": 4, "episodes": 8, "name": "Season 4"}], # The Boys
    119051: [{"season": 1, "episodes": 8, "name": "Season 1"}], # Wednesday
    71446: [{"season": 1, "episodes": 13, "name": "Part 1"}, {"season": 2, "episodes": 9, "name": "Part 2"}, {"season": 3, "episodes": 8, "name": "Part 3"}, {"season": 4, "episodes": 8, "name": "Part 4"}, {"season": 5, "episodes": 10, "name": "Part 5"}], # Money Heist
    100088: [{"season": 1, "episodes": 9, "name": "Season 1"}], # The Last of Us
    84958: [{"season": 1, "episodes": 6, "name": "Season 1"}, {"season": 2, "episodes": 6, "name": "Season 2"}], # Loki
    1396: [{"season": 1, "episodes": 7, "name": "Season 1"}, {"season": 2, "episodes": 13, "name": "Season 2"}, {"season": 3, "episodes": 13, "name": "Season 3"}, {"season": 4, "episodes": 13, "name": "Season 4"}, {"season": 5, "episodes": 16, "name": "Season 5"}], # Breaking Bad
    1399: [{"season": 1, "episodes": 10, "name": "Season 1"}, {"season": 2, "episodes": 10, "name": "Season 2"}, {"season": 3, "episodes": 10, "name": "Season 3"}, {"season": 4, "episodes": 10, "name": "Season 4"}, {"season": 5, "episodes": 10, "name": "Season 5"}, {"season": 6, "episodes": 10, "name": "Season 6"}, {"season": 7, "episodes": 7, "name": "Season 7"}, {"season": 8, "episodes": 6, "name": "Season 8"}], # Game of Thrones
}

def get_real_seasons_data(title, media_type="tv", tmdb_id=None):
    if media_type == "movie":
        return []
    
    if tmdb_id and tmdb_id in _KNOWN_SEASONS:
        return _KNOWN_SEASONS[tmdb_id]

    seasons = []
    if title:
        t_low = title.lower().strip()
        for kid, kseasons in _KNOWN_SEASONS.items():
            k_item = next((m for m in CATALOG if m.get("id") == kid), None)
            if k_item and k_item.get("title", "").lower().strip() in t_low:
                return kseasons

        try:
            q = urllib.parse.quote_plus(title.strip())
            r = requests.get(f"https://api2.imdb4.shop/api/search2/{q}?page=0", headers=headers_tmdb, timeout=0.6)
            if r.status_code == 200:
                res = r.json().get("results", [])
                if res:
                    m_type = res[0].get("media_type", "tv")
                    m_id = res[0].get("id")
                    r2 = requests.get(f"https://api2.imdb4.shop/api/{m_type}/{m_id}", headers=headers_tmdb, timeout=0.6)
                    if r2.status_code == 200:
                        det = r2.json().get("results", [{}])[0]
                        for s in det.get("season", []):
                            se_num = s.get("se", 1)
                            ep_num = s.get("ep") or 8
                            if se_num > 0:
                                seasons.append({
                                    "season": se_num,
                                    "episodes": ep_num,
                                    "name": f"Season {se_num}"
                                })
        except Exception:
            pass

    if not seasons and media_type != "movie":
        seasons = [{"season": 1, "episodes": 8, "name": "Season 1"}]
    return seasons

def fetch_tmdb_extended(movie_id, media_type="movie"):
    cache_key = f"{media_type}_{movie_id}"
    if cache_key in _extended_cache:
        return _extended_cache[cache_key]

    m_types_to_try = ["tv", "movie"] if media_type in ["tv", "series"] else ["movie", "tv"]
    for m_type in m_types_to_try:
        try:
            url = f"{api.TMDB_BASE_URL}/{m_type}/{movie_id}"
            params = {
                "api_key": api.TMDB_API_KEY,
                "append_to_response": "aggregate_credits,credits,videos"
            }
            res = requests.get(url, params=params, headers=headers_tmdb, timeout=2.0)
            if res.status_code == 200:
                data = res.json()
                cast_list = []
                
                raw_cast = data.get("aggregate_credits", {}).get("cast", []) or data.get("credits", {}).get("cast", [])
                for c in raw_cast[:10]:
                    photo = f"https://image.tmdb.org/t/p/w200{c['profile_path']}" if c.get("profile_path") else None
                    char_role = c.get("character")
                    if not char_role and c.get("roles"):
                        char_role = c["roles"][0].get("character")
                    cast_list.append({
                        "name": c.get("name"),
                        "character": char_role or "Main Role",
                        "photo": photo
                    })
                
                genres = [g.get("name") for g in data.get("genres", [])]
                raw_date = data.get("release_date") or data.get("first_air_date") or "2024"
                formatted_date = format_release_date(raw_date)
                
                prod_countries = data.get("production_countries", [])
                origin_countries = data.get("origin_country", [])
                country_name = "International"
                if origin_countries:
                    c_code = origin_countries[0]
                    country_name = "Korea" if c_code == "KR" else ("Japan" if c_code == "JP" else ("India" if c_code == "IN" else ("China" if c_code == "CN" else ("USA" if c_code == "US" else ("UK" if c_code == "GB" else c_code)))))
                elif prod_countries:
                    country_name = prod_countries[0].get("name", "International")

                trailer_obj = None
                for v in data.get("videos", {}).get("results", []):
                    if v.get("site") == "YouTube" and v.get("type") in ["Trailer", "Teaser", "Clip"]:
                        trailer_obj = {
                            "name": v.get("name", "Official Trailer"),
                            "embed_url": f"https://www.youtube.com/embed/{v.get('key')}?rel=0",
                            "youtube_key": v.get("key")
                        }
                        if v.get("type") == "Trailer":
                            break

                seasons_from_tmdb = []
                if m_type == "tv":
                    for s_item in data.get("seasons", []):
                        s_num = s_item.get("season_number", 0)
                        ep_c = s_item.get("episode_count", 0)
                        if s_num > 0 and ep_c > 0:
                            p_path = s_item.get("poster_path")
                            seasons_from_tmdb.append({
                                "season": s_num,
                                "episodes": ep_c,
                                "name": s_item.get("name") or f"Season {s_num}",
                                "poster": f"https://image.tmdb.org/t/p/w500{p_path}" if p_path else None,
                                "overview": s_item.get("overview", "")
                            })

                b_path = data.get("backdrop_path")
                backdrop_url = f"https://image.tmdb.org/t/p/w1280{b_path}" if b_path else None

                res_data = {
                    "title": data.get("title") or data.get("name"),
                    "overview": data.get("overview"),
                    "release_date": formatted_date,
                    "rating": round(float(data.get("vote_average", 7.5)), 1),
                    "genres": genres,
                    "cast": cast_list,
                    "country": country_name,
                    "trailer": trailer_obj,
                    "detected_type": m_type,
                    "seasons": seasons_from_tmdb,
                    "backdrop": backdrop_url
                }
                _extended_cache[cache_key] = res_data
                return res_data
        except Exception as e:
            print("Extended details error:", e)
    return None

def fetch_season_episodes(tv_id: int, season_num: int):
    cache_k = f"season_eps_{tv_id}_{season_num}"
    if cache_k in _extended_cache:
        return _extended_cache[cache_k]
    try:
        url = f"{api.TMDB_BASE_URL}/tv/{tv_id}/season/{season_num}"
        res = requests.get(url, params={"api_key": api.TMDB_API_KEY}, headers=headers_tmdb, timeout=2.0)
        if res.status_code == 200:
            s_data = res.json()
            p_path = s_data.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{p_path}" if p_path else None
            ep_list = []
            for ep in s_data.get("episodes", []):
                st = ep.get("still_path")
                ep_list.append({
                    "episode_number": ep.get("episode_number"),
                    "name": ep.get("name") or f"Episode {ep.get('episode_number')}",
                    "still": f"https://image.tmdb.org/t/p/w780{st}" if st else None,
                    "overview": ep.get("overview", "")
                })
            res_obj = {
                "season_name": s_data.get("name"),
                "poster": poster_url,
                "overview": s_data.get("overview", ""),
                "episodes": ep_list
            }
            _extended_cache[cache_k] = res_obj
            return res_obj
    except Exception as e:
        print("Season episodes error:", e)
    return None

@app.get("/api/movie/{movie_id}")
def get_movie_detail(movie_id: int, type: Optional[str] = None, s: Optional[int] = 1, e: Optional[int] = 1):
    # Find in local catalog
    item = next((m for m in CATALOG if m.get("id") == movie_id), None)
    
    # Source of truth for media_type:
    # 1. If catalog item exists and specifies media_type (e.g. tv), respect it!
    # 2. If explicit query parameter type is "tv" or "series", use tv
    # 3. If tmdb_id is in _KNOWN_SEASONS, it is a TV show
    if item and item.get("media_type") in ["tv", "series"]:
        media_type = "tv"
    elif movie_id in _KNOWN_SEASONS:
        media_type = "tv"
    elif type and type in ["tv", "series"]:
        media_type = "tv"
    elif item and item.get("media_type"):
        media_type = item.get("media_type")
    elif type and type == "movie":
        media_type = "movie"
    else:
        media_type = "movie"
    
    # Try fetching extended TMDB info (cast, trailer, accurate genres, release date, seasons)
    ext = fetch_tmdb_extended(movie_id, media_type)
    if ext and ext.get("detected_type"):
        media_type = ext["detected_type"]
    
    if not item:
        item = {
            "id": movie_id,
            "title": ext.get("title", "Movie Details") if ext else "Movie Details",
            "clean_title": ext.get("title", "Movie Details") if ext else "Movie Details",
            "media_type": media_type,
            "rating": ext.get("rating", 7.5) if ext else 7.5,
            "year": "2024",
            "country": ext.get("country", "International") if ext else "International",
            "genres": ext.get("genres", ["Feature"]) if ext else ["Feature"],
            "overview": ext.get("overview", "") if ext else ""
        }
    else:
        item = dict(item)
        if ext:
            if ext.get("genres"): item["genres"] = ext["genres"]
            if ext.get("overview"): item["overview"] = ext["overview"]
            if ext.get("country") and ext["country"] != "International": item["country"] = ext["country"]
            if ext.get("release_date"): item["release_date"] = ext["release_date"]
            if ext.get("rating"): item["rating"] = ext["rating"]
            
    if "release_date" not in item:
        item["release_date"] = format_release_date(item.get("year", "2024") + "-01-01")
        
    cast = ext.get("cast", []) if ext else []
    trailer = ext.get("trailer") if ext and ext.get("trailer") else stream.get_trailer_url(movie_id, media_type, title=item.get("title"))
    # Authorized Direct Stream (Video.js, HLS/MP4/Cloudflare Stream, Internet Archive)
    real_tmdb_id = item.get("tmdb_id") or movie_id if item else movie_id
    direct_stream = db.get_video_stream(real_tmdb_id) or stream.get_direct_stream(real_tmdb_id, item.get("title"))
    streaming_servers = stream.get_streaming_servers(real_tmdb_id, media_type, season=s, episode=e, direct_url=direct_stream.get("playback_url") if direct_stream else None)
    providers = api.fetch_streaming_providers(media_type, movie_id, "IN")
    recs = rec.get_ml_recommendations(movie_id, item.get("title"), limit=12)
    history_items = db.get_history(50)
    user_history = next((h for h in history_items if h.get("tmdb_id") == movie_id), None)
    resume_seconds = user_history.get("progress_seconds", 0) if user_history else 0
    duration_seconds = user_history.get("duration_seconds", 0) if user_history else 0

    # Real seasons and episodes (NetMirror / TMDB Grounded)
    seasons = ext.get("seasons", []) if ext else []
    if media_type != "movie" and not seasons:
        seasons = get_real_seasons_data(item.get("title"), media_type, tmdb_id=movie_id)
    elif media_type == "movie":
        seasons = []

    if ext and ext.get("backdrop"):
        item["backdrop"] = ext["backdrop"]

    # Fetch active season and episode thumbnails dynamically
    active_season_info = None
    episodes_info = []
    current_thumbnail = item.get("backdrop") or item.get("poster")
    if media_type != "movie":
        active_season_info = fetch_season_episodes(movie_id, s or 1)
        if active_season_info:
            episodes_info = active_season_info.get("episodes", [])
            s_poster = active_season_info.get("poster")
            if s_poster:
                item["poster"] = s_poster
                item["season_poster"] = s_poster
            # Find current episode still
            matching_ep = next((ep for ep in episodes_info if ep.get("episode_number") == (e or 1)), None)
            if matching_ep and matching_ep.get("still"):
                current_thumbnail = matching_ep["still"]
            elif s_poster:
                current_thumbnail = s_poster
        elif seasons:
            match_s = next((sec for sec in seasons if sec.get("season") == (s or 1)), None)
            if match_s and match_s.get("poster"):
                item["poster"] = match_s["poster"]
                item["season_poster"] = match_s["poster"]
                current_thumbnail = match_s["poster"]

        if not episodes_info and seasons:
            match_s = next((sec for sec in seasons if sec.get("season") == (s or 1)), seasons[0])
            total_eps = match_s.get("episodes", 8)
            episodes_info = [
                {
                    "episode_number": ep_num,
                    "name": f"Episode {ep_num}",
                    "still": current_thumbnail,
                    "overview": f"Episode {ep_num} of Season {s or 1}"
                }
                for ep_num in range(1, total_eps + 1)
            ]
    
    return {
        "item": item,
        "media_type": media_type,
        "season": s,
        "episode": e,
        "seasons": seasons,
        "active_season_info": active_season_info,
        "episodes_info": episodes_info,
        "current_thumbnail": current_thumbnail,
        "genres": item.get("genres", ["Movie"]),
        "cast": cast,
        "direct_stream": direct_stream,
        "resume_seconds": resume_seconds,
        "duration_seconds": duration_seconds,
        "streaming_servers": streaming_servers,
        "trailer": trailer,
        "watch_providers": providers,
        "recommendations": recs
    }

@app.get("/api/recommend/status")
def get_recommender_status():
    """Returns runtime model health, metadata, and active recommendation engine."""
    return rec.get_recommender_status()

@app.get("/api/recommend/{movie_id}")
def get_recommendations(movie_id: int, title: Optional[str] = None):
    recs, engine_used = rec.get_recommendations_with_meta(movie_id, title, limit=12)
    return {
        "movie_id": movie_id,
        "engine_used": engine_used,
        "count": len(recs),
        "results": recs
    }

# Direct Streaming Catalog Endpoints (Protected by Admin API Key & URL validation)
@app.post("/api/streams")
def add_custom_stream(
    inp: CustomStreamInput,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")
):
    # 1. Admin Authentication Check
    admin_secret = os.getenv("ADMIN_API_KEY")
    if admin_secret:
        if not x_admin_key or x_admin_key != admin_secret:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid or missing X-Admin-Key")
    
    # 2. URL Scheme Validation (Only allow secure http, https, hls streams)
    parsed = urlparse(inp.playback_url)
    if parsed.scheme not in ["http", "https"]:
        raise HTTPException(status_code=400, detail="Invalid playback_url scheme. Only HTTP/HTTPS protocols allowed.")
    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid playback_url host.")

    # 3. Save to database
    db.set_video_stream(inp.tmdb_id, inp.title, inp.playback_type, inp.playback_url, 1, inp.subtitles)
    return {"status": "success", "message": f"Authorized stream registered for {inp.title}"}

@app.get("/api/streams/{tmdb_id}")
def get_stream(tmdb_id: int):
    st = db.get_video_stream(tmdb_id)
    if not st:
        raise HTTPException(status_code=404, detail="No direct stream found for this title")
    return st

# Watchlist Endpoints
@app.get("/api/watchlist")
def get_watchlist():
    return db.get_watchlist()

@app.post("/api/watchlist")
def add_watchlist(item: WatchItem):
    db.add_to_watchlist(item.dict())
    return {"status": "success", "message": f"Added {item.title} to watchlist"}

@app.delete("/api/watchlist/{tmdb_id}")
def delete_watchlist(tmdb_id: int):
    db.remove_from_watchlist(tmdb_id)
    return {"status": "success", "message": "Removed from watchlist"}

# Watch History & Playback Progress Endpoints (Step 6 & 8)
@app.get("/api/history")
def get_history():
    return db.get_history()

@app.post("/api/history")
def add_history(item: WatchItem):
    db.add_to_history(item.dict())
    return {"status": "success", "message": "History updated"}

@app.post("/api/history/{tmdb_id}/progress")
def update_playback_progress(
    tmdb_id: int,
    update: ProgressUpdate,
    x_user_id: Optional[str] = Header("default_user", alias="X-User-Id")
):
    db.update_playback_progress(
        tmdb_id,
        update.progress_seconds,
        update.duration_seconds,
        user_id=x_user_id or "default_user",
        season=update.season or 1,
        episode=update.episode or 1
    )
    return {"status": "ok", "tmdb_id": tmdb_id, "progress": update.progress_seconds}

@app.delete("/api/history")
def clear_history(x_user_id: Optional[str] = Header("default_user", alias="X-User-Id")):
    db.clear_history(user_id=x_user_id or "default_user")
    return {"status": "success", "message": "History cleared"}
