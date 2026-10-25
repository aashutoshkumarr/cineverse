import os
import requests
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TVMAZE_BASE_URL = "https://api.tvmaze.com"
ANILIST_URL = "https://graphql.anilist.co"

# Genre mapping
GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
    10759: "Action & Adventure", 10762: "Kids", 10763: "News", 10764: "Reality",
    10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk", 10768: "War & Politics"
}

# Country config
COUNTRY_CONFIG = {
    "India": {"origin_country": "IN", "langs": ["hi", "te", "ta", "ml"]},
    "USA": {"origin_country": "US", "langs": ["en"]},
    "UK": {"origin_country": "GB", "langs": ["en"]},
    "Korea": {"origin_country": "KR", "langs": ["ko"]},
    "Japan": {"origin_country": "JP", "langs": ["ja"]},
    "China": {"origin_country": "CN", "langs": ["zh"]},
    "Bangladesh": {"origin_country": "BD", "langs": ["bn"]}
}

# Category config
CATEGORY_CONFIG = {
    "Animation": {"genre_id": 16, "media_type": "all"},
    "Anime": {"genre_id": 16, "origin_country": "JP", "media_type": "tv"},
    "Hindi": {"lang": "hi", "origin_country": "IN"},
    "Telugu": {"lang": "te", "origin_country": "IN"},
    "Tamil": {"lang": "ta", "origin_country": "IN"},
    "Malayalam": {"lang": "ml", "origin_country": "IN"},
    "K-Drama": {"lang": "ko", "origin_country": "KR", "media_type": "tv"},
    "C-Drama": {"lang": "zh", "origin_country": "CN", "media_type": "tv"},
    "Hollywood": {"lang": "en", "origin_country": "US"}
}

def get_svg_fallback(title, cat="Movie"):
    clean_title = title.replace("[", "").replace("]", "").strip()[:20]
    svg_code = f"""<svg xmlns="http://www.w3.org/2000/svg" width="500" height="750" viewBox="0 0 500 750">
        <defs>
            <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#0b1b36"/>
                <stop offset="50%" stop-color="#041226"/>
                <stop offset="100%" stop-color="#020916"/>
            </linearGradient>
            <linearGradient id="acc" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#f97316"/>
                <stop offset="100%" stop-color="#00e676"/>
            </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#bg)"/>
        <rect x="25" y="25" width="450" height="700" rx="16" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="2"/>
        <circle cx="250" cy="300" r="75" fill="rgba(255,255,255,0.04)" stroke="url(#acc)" stroke-width="3"/>
        <text x="250" y="325" font-family="sans-serif" font-size="52" text-anchor="middle" fill="#ffffff">🎬</text>
        <text x="250" y="440" font-family="sans-serif" font-size="28" font-weight="bold" text-anchor="middle" fill="#ffffff">{clean_title}</text>
        <text x="250" y="480" font-family="sans-serif" font-size="16" text-anchor="middle" fill="#94a3b8">{cat} • Ultra HD</text>
        <rect x="160" y="520" width="180" height="36" rx="18" fill="url(#acc)"/>
        <text x="250" y="544" font-family="sans-serif" font-size="14" font-weight="bold" text-anchor="middle" fill="#ffffff">MovieRecommender</text>
    </svg>"""
    return f"data:image/svg+xml;utf8,{urllib.parse.quote(svg_code)}"

def search_tmdb_multi(query):
    """Live search across movies, TV series and animations on TMDB."""
    try:
        url = f"{TMDB_BASE_URL}/search/multi"
        params = {
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "en-US",
            "page": 1,
            "include_adult": False
        }
        res = requests.get(url, params=params, timeout=2.5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            items = []
            for m in results:
                m_type = m.get("media_type")
                if m_type not in ["movie", "tv"]:
                    continue
                title = m.get("title") or m.get("name") or "Untitled"
                p = m.get("poster_path")
                poster = f"https://image.tmdb.org/t/p/w500{p}" if p else get_svg_fallback(title, "Movie")
                vote = round(float(m.get("vote_average", 7.5)), 1)
                date = (m.get("release_date") or m.get("first_air_date") or "2024")[:4]
                genre_ids = m.get("genre_ids", [])
                genres = [GENRE_MAP.get(gid, "Movie") for gid in genre_ids[:2]]

                orig_lang = m.get("original_language", "en")
                badge = "Hindi" if orig_lang == "hi" else ("K-Drama" if orig_lang == "ko" else ("Anime" if 16 in genre_ids and orig_lang == "ja" else "HD"))

                items.append({
                    "id": m.get("id"),
                    "title": title,
                    "clean_title": title,
                    "media_type": m_type,
                    "poster": poster,
                    "rating": vote if vote > 0 else 7.5,
                    "year": date,
                    "badge": badge,
                    "genres": genres,
                    "overview": m.get("overview", "No overview available.")
                })
            return items
    except Exception as e:
        print("Search TMDB error:", e)
    return []

def fetch_tmdb_recommendations(media_type, media_id):
    """Fetches real-time recommendations or similar titles from TMDB for an exact ID."""
    try:
        url = f"{TMDB_BASE_URL}/{media_type}/{media_id}/recommendations"
        params = {"api_key": TMDB_API_KEY, "language": "en-US", "page": 1}
        res = requests.get(url, params=params, timeout=2.5)
        results = []
        if res.status_code == 200:
            results = res.json().get("results", [])

        if not results:
            # Fallback to similar
            url_sim = f"{TMDB_BASE_URL}/{media_type}/{media_id}/similar"
            res_sim = requests.get(url_sim, params=params, timeout=2.5)
            if res_sim.status_code == 200:
                results = res_sim.json().get("results", [])

        items = []
        for m in results[:12]:
            title = m.get("title") or m.get("name") or "Untitled"
            p = m.get("poster_path")
            poster = f"https://image.tmdb.org/t/p/w500{p}" if p else get_svg_fallback(title, "Movie")
            vote = round(float(m.get("vote_average", 7.5)), 1)
            date = (m.get("release_date") or m.get("first_air_date") or "2024")[:4]
            items.append({
                "id": m.get("id"),
                "title": title,
                "clean_title": title,
                "media_type": media_type,
                "poster": poster,
                "rating": vote if vote > 0 else 7.5,
                "year": date,
                "badge": "Matched",
                "overview": m.get("overview", "")
            })
        return items
    except Exception as e:
        print("Fetch recommendations error:", e)
    return []

def fetch_tmdb_discover(country="All", category="All", language="All", page=1):
    """Fetches titles dynamically from TMDB discover API with country and category filters."""
    try:
        media_type = "movie"
        params = {
            "api_key": TMDB_API_KEY,
            "page": page,
            "sort_by": "popularity.desc",
            "vote_count.gte": 15
        }

        # Apply Category
        if category in CATEGORY_CONFIG:
            cfg = CATEGORY_CONFIG[category]
            if "media_type" in cfg:
                media_type = cfg["media_type"]
                if media_type == "all":
                    media_type = "movie"
            if "genre_id" in cfg:
                params["with_genres"] = cfg["genre_id"]
            if "lang" in cfg:
                params["with_original_language"] = cfg["lang"]
            if "origin_country" in cfg:
                params["with_origin_country"] = cfg["origin_country"]

        # Apply Country
        if country in COUNTRY_CONFIG:
            c_cfg = COUNTRY_CONFIG[country]
            params["with_origin_country"] = c_cfg["origin_country"]
            if "with_original_language" not in params:
                params["with_original_language"] = c_cfg["langs"][0]

        # Apply Language
        if language == "Hindi":
            params["with_original_language"] = "hi"
        elif language == "English":
            params["with_original_language"] = "en"

        url = f"{TMDB_BASE_URL}/discover/{media_type}"
        res = requests.get(url, params=params, timeout=2.5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            items = []
            for m in results:
                title = m.get("title") or m.get("name") or "Untitled"
                p = m.get("poster_path")
                poster = f"https://image.tmdb.org/t/p/w500{p}" if p else get_svg_fallback(title, category)
                vote = round(float(m.get("vote_average", 7.5)), 1)
                date = (m.get("release_date") or m.get("first_air_date") or "2024")[:4]
                items.append({
                    "id": m.get("id"),
                    "title": title,
                    "clean_title": title,
                    "poster": poster,
                    "rating": vote if vote > 0 else 7.5,
                    "year": date,
                    "badge": language if language != "All" else ("HD" if vote >= 7.0 else "4K"),
                    "country": country if country != "All" else "International",
                    "category": category if category != "All" else "Popular",
                    "languages": ["Hindi" if params.get("with_original_language") == "hi" else "English"],
                    "media_type": media_type,
                    "overview": m.get("overview", "")
                })
            return items
    except Exception as e:
        print("TMDB Discover error:", e)
    return []

def fetch_streaming_providers(media_type, tmdb_id, country_code="IN"):
    """Fetches where to watch (Netflix, JioHotstar, Prime, etc.) via TMDB watch providers."""
    try:
        url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/watch/providers?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=2.0)
        if res.status_code == 200:
            results = res.json().get("results", {})
            region = results.get(country_code, results.get("US", {}))
            providers = []
            for p in region.get("flatrate", [])[:4]:
                providers.append(p.get("provider_name"))
            if not providers:
                for p in region.get("buy", [])[:3]:
                    providers.append(p.get("provider_name"))
            return providers
    except Exception:
        pass
    return ["Netflix", "Prime Video"]

def fetch_anilist_trending(page=1, per_page=12):
    """Fetches trending anime from AniList GraphQL API."""
    query = """
    query ($page: Int, $perPage: Int) {
      Page (page: $page, perPage: $perPage) {
        media (type: ANIME, sort: TRENDING_DESC) {
          id
          title {
            english
            romaji
          }
          averageScore
          startDate {
            year
          }
          coverImage {
            large
          }
          genres
          description
        }
      }
    }
    """
    try:
        res = requests.post(ANILIST_URL, json={'query': query, 'variables': {'page': page, 'perPage': per_page}}, timeout=2.5)
        if res.status_code == 200:
            data = res.json().get('data', {}).get('Page', {}).get('media', [])
            items = []
            for a in data:
                t = a.get('title', {}).get('english') or a.get('title', {}).get('romaji') or "Anime"
                score = round((a.get('averageScore') or 80) / 10.0, 1)
                year = str(a.get('startDate', {}).get('year') or "2024")
                img = a.get('coverImage', {}).get('large') or get_svg_fallback(t, "Anime")
                items.append({
                    "id": a.get("id"),
                    "title": t,
                    "clean_title": t,
                    "poster": img,
                    "rating": score,
                    "year": year,
                    "badge": "Anime",
                    "country": "Japan",
                    "category": "Anime",
                    "languages": ["Japanese", "Hindi", "English"],
                    "source": "AniList"
                })
            return items
    except Exception as e:
        print("AniList error:", e)
    return []

def fetch_tvmaze_shows(query):
    """Search TV series via TVmaze API (no API key needed)."""
    try:
        url = f"{TVMAZE_BASE_URL}/search/shows?q={urllib.parse.quote(query)}"
        res = requests.get(url, timeout=2.5)
        if res.status_code == 200:
            results = res.json()
            items = []
            for item in results[:10]:
                show = item.get("show", {})
                t = show.get("name")
                img_obj = show.get("image") or {}
                img = img_obj.get("medium") or img_obj.get("original") or get_svg_fallback(t, "TV")
                rating_obj = show.get("rating") or {}
                rating = rating_obj.get("average") or 7.8
                premiered = (show.get("premiered") or "2024")[:4]
                country = (show.get("network") or {}).get("country", {}).get("name") or "International"
                items.append({
                    "id": show.get("id"),
                    "title": t,
                    "clean_title": t,
                    "poster": img,
                    "rating": round(float(rating), 1),
                    "year": premiered,
                    "badge": "TV Series",
                    "country": country,
                    "category": "K-Drama" if country == "Korea" else "Hollywood",
                    "languages": ["English"],
                    "source": "TVmaze",
                    "official_site": show.get("officialSite")
                })
            return items
    except Exception as e:
        print("TVmaze error:", e)
    return []
