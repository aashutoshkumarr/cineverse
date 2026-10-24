import os
import sys
import json
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Add parent directory to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

import api_service as api
from backend import database as db
from backend import recommender as rec
from backend import streaming_service as stream

app = FastAPI(title="Cineverse API", version="2.0.0")

# Enable CORS for React frontend (Vite defaults to port 5173 or any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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

class CustomStreamInput(BaseModel):
    tmdb_id: int
    title: str
    playback_type: str = "hls"
    playback_url: str
    subtitles: Optional[str] = None

@app.get("/api/health")
def health():
    return {"status": "ok", "total_catalog": len(CATALOG)}

@app.get("/api/movies")
def get_movies(
    page: int = 1,
    limit: int = 24,
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

    # Trending Now
    shelves.append({"id": "trending", "title": "🔥 Trending Now on Cineverse", "tag": "TMDB Popular", "items": take(CATALOG, 10)})
    
    # Curated categories
    cartoons = [m for m in CATALOG if m.get("category") == "Animation"]
    anime = [m for m in CATALOG if m.get("category") == "Anime"]
    kdrama = [m for m in CATALOG if m.get("country") == "Korea"]
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
from datetime import datetime

_extended_cache = {}
headers_tmdb = {"User-Agent": "Mozilla/5.0"}

def format_release_date(date_str):
    if not date_str:
        return "2024"
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return date_str

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
            res = requests.get(url, params=params, headers=headers_tmdb, timeout=4.5)
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

                res_data = {
                    "title": data.get("title") or data.get("name"),
                    "overview": data.get("overview"),
                    "release_date": formatted_date,
                    "rating": round(float(data.get("vote_average", 7.5)), 1),
                    "genres": genres,
                    "cast": cast_list,
                    "country": country_name,
                    "trailer": trailer_obj,
                    "detected_type": m_type
                }
                _extended_cache[cache_key] = res_data
                return res_data
        except Exception as e:
            print("Extended details error:", e)
    return None

@app.get("/api/movie/{movie_id}")
def get_movie_detail(movie_id: int, type: Optional[str] = "movie", s: Optional[int] = 1, e: Optional[int] = 1):
    # Find in local catalog
    item = next((m for m in CATALOG if m.get("id") == movie_id), None)
    media_type = type or (item.get("media_type") if item else "movie")
    
    # Try fetching extended TMDB info (cast, trailer, accurate genres, release date)
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
    trailer = stream.get_trailer_url(movie_id, media_type, title=item.get("title"))
    if not trailer and ext:
        trailer = ext.get("trailer")
    streaming_servers = stream.get_streaming_servers(movie_id, media_type, season=s, episode=e)
    providers = api.fetch_streaming_providers(media_type, movie_id, "IN")
    recs = rec.get_ml_recommendations(movie_id, item.get("title"), limit=12)
    
    # Authorized Direct Stream (HLS/MP4/Cloudflare Stream) from video_catalog
    direct_stream = db.get_video_stream(movie_id)
    history_items = db.get_history(50)
    user_history = next((h for h in history_items if h.get("tmdb_id") == movie_id), None)
    resume_seconds = user_history.get("progress_seconds", 0) if user_history else 0
    duration_seconds = user_history.get("duration_seconds", 0) if user_history else 0
    
    return {
        "item": item,
        "media_type": media_type,
        "season": s,
        "episode": e,
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

@app.get("/api/recommend/{movie_id}")
def get_recommendations(movie_id: int, title: Optional[str] = None):
    recs = rec.get_ml_recommendations(movie_id, title, limit=12)
    return {"movie_id": movie_id, "results": recs}

# Direct Streaming Catalog Endpoints (Step 3 & 4)
@app.post("/api/streams")
def add_custom_stream(inp: CustomStreamInput):
    db.set_video_stream(inp.tmdb_id, inp.title, inp.playback_type, inp.playback_url, 1, inp.subtitles)
    return {"status": "success", "message": f"Authorized stream saved for {inp.title}"}

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
def update_playback_progress(tmdb_id: int, update: ProgressUpdate):
    db.update_playback_progress(tmdb_id, update.progress_seconds, update.duration_seconds)
    return {"status": "ok", "tmdb_id": tmdb_id, "progress": update.progress_seconds}

@app.delete("/api/history")
def clear_history():
    db.clear_history()
    return {"status": "success", "message": "History cleared"}
    return {"status": "success", "message": "History cleared"}
