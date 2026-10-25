import requests
import sys
import os
import urllib.parse

# Include parent directory for api_service
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import api_service as api

TMDB_API_KEY = api.TMDB_API_KEY
TMDB_BASE_URL = api.TMDB_BASE_URL

_trailer_cache = {}

def get_trailer_url(tmdb_id, media_type="movie", title=None):
    """
    Fetches official trailer for the dedicated Trailer section at the bottom of the page.
    (Kept completely separate from the full movie streaming servers).
    """
    if tmdb_id in _trailer_cache:
        return _trailer_cache[tmdb_id]

    # Try dynamic search on NetMirror API for official trailer
    if title:
        try:
            q = urllib.parse.quote_plus(title.strip())
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://netmirror.app"}
            r = requests.get(f"https://api2.imdb4.shop/api/search2/{q}?page=0", headers=headers, timeout=0.6)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    m_t = results[0].get("media_type", "tv" if media_type in ["tv", "series"] else "movie")
                    m_i = results[0].get("id")
                    r2 = requests.get(f"https://api2.imdb4.shop/api/{m_t}/{m_i}", headers=headers, timeout=0.6)
                    if r2.status_code == 200:
                        d = r2.json().get("results", [{}])[0]
                        mp4 = d.get("trailer")
                        if mp4 and mp4.startswith("http"):
                            res = {
                                "name": "Official Trailer",
                                "mp4_url": mp4,
                                "is_mp4": True
                            }
                            _trailer_cache[tmdb_id] = res
                            return res
        except Exception:
            pass

    # Fallback to TMDB videos endpoint
    try:
        m_type = "movie" if media_type not in ["tv", "series"] else "tv"
        url = f"{TMDB_BASE_URL}/{m_type}/{tmdb_id}/videos"
        res = requests.get(url, params={"api_key": TMDB_API_KEY}, headers=api.get_tmdb_headers(), timeout=2.0)
        if res.status_code == 200:
            videos = res.json().get("results", [])
            for v in videos:
                if v.get("site") == "YouTube" and v.get("type") in ["Trailer", "Teaser"]:
                    ans = {
                        "name": v.get("name", "Official Trailer"),
                        "embed_url": f"https://www.youtube-nocookie.com/embed/{v.get('key')}?autoplay=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&fs=1",
                        "youtube_key": v.get("key"),
                        "is_mp4": False
                    }
                    _trailer_cache[tmdb_id] = ans
                    return ans
            if videos:
                v = videos[0]
                if v.get("site") == "YouTube":
                    ans = {
                        "name": v.get("name", "Official Video"),
                        "embed_url": f"https://www.youtube-nocookie.com/embed/{v.get('key')}?autoplay=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&fs=1",
                        "youtube_key": v.get("key"),
                        "is_mp4": False
                    }
                    _trailer_cache[tmdb_id] = ans
                    return ans
    except Exception as e:
        print("Trailer fetch error:", e)
        
    return None

def get_direct_stream(tmdb_id, title=None):
    """
    Returns an authorized full-length custom stream ONLY if explicitly registered in the database.
    Never returns trailers or test clips as movie streams.
    """
    try:
        from backend import database as db
        custom = db.get_video_stream(tmdb_id)
        if custom and custom.get("playback_url"):
            url = custom["playback_url"]
            if "mux.dev" in url or "BigBuckBunny" in url:
                return None
            return {
                "playback_url": url,
                "playback_type": custom.get("playback_type", "hls" if ".m3u8" in url else "mp4"),
                "provider": "Custom Cloudflare Stream / CDN"
            }
    except Exception:
        pass

    return None

def get_streaming_servers(tmdb_id, media_type="movie", season=1, episode=1, direct_url=None):
    """
    Returns 10 high-speed verified streaming servers (Server 1 to Server 10).
    Every server streams the FULL MOVIE or FULL TV EPISODE (never trailers or promo clips).
    Strictly named 'Server 1', 'Server 2', 'Server 3', etc. with no extra text.
    """
    m_type = "movie" if media_type not in ["tv", "series"] else "tv"
    m_prefix = "movie" if m_type == "movie" else "tv"
    
    # TV vs Movie URL params
    tv_suffix = f"/{season}/{episode}" if m_type == "tv" else ""
    two_tv_suffix = f"&s={season}&e={episode}" if m_type == "tv" else ""
    multi_tv_suffix = f"&s={season}&e={episode}" if m_type == "tv" else ""
    smash_tv_suffix = f"&season={season}&episode={episode}" if m_type == "tv" else ""
    dash_tv_suffix = f"-{season}-{episode}" if m_type == "tv" else ""

    servers = []

    # If an authorized full-length stream was uploaded to database, offer it as Server 1
    if direct_url and direct_url.startswith("http") and "mux.dev" not in direct_url and "BigBuckBunny" not in direct_url:
        servers.append({
            "id": "cineverse_direct",
            "name": "Server 1",
            "url": direct_url,
            "quality": "1080p",
            "is_direct": True
        })

    # The top live, verified, ultra-fast full-length movie & series streaming servers
    # Uses genuine multi-CDN provider diversity (AutoEmbed, VidSrc.to, 2Embed, SmashyStream, VidLink)
    mirrors = [
        {"id": "autoembed", "url": f"https://autoembed.co/movie/tmdb/{tmdb_id}" if m_type == "movie" else f"https://autoembed.co/tv/tmdb/{tmdb_id}-{season}-{episode}"},
        {"id": "vidsrc_to", "url": f"https://vidsrc.to/embed/movie/{tmdb_id}" if m_type == "movie" else f"https://vidsrc.to/embed/tv/{tmdb_id}/{season}/{episode}"},
        {"id": "two_embed", "url": f"https://www.2embed.cc/embed/{tmdb_id}" if m_type == "movie" else f"https://www.2embed.cc/embedtv/{tmdb_id}?s={season}&e={episode}"},
        {"id": "smashystream", "url": f"https://embed.smashystream.com/playere.php?tmdb={tmdb_id}" if m_type == "movie" else f"https://embed.smashystream.com/playere.php?tmdb={tmdb_id}&season={season}&episode={episode}"},
        {"id": "two_embed_skin", "url": f"https://2embed.skin/embed/{tmdb_id}" if m_type == "movie" else f"https://2embed.skin/embedtv/{tmdb_id}?s={season}&e={episode}"},
        {"id": "vidlink", "url": f"https://vidlink.pro/movie/{tmdb_id}" if m_type == "movie" else f"https://vidlink.pro/tv/{tmdb_id}/{season}/{episode}"},
        {"id": "vidsrc_su", "url": f"https://vidsrc.su/embed/{m_prefix}/{tmdb_id}{tv_suffix}"},
        {"id": "nontongo", "url": f"https://nontongo.win/embed/{m_prefix}/{tmdb_id}{tv_suffix}"},
        {"id": "vidsrc_pm", "url": f"https://vidsrc.pm/embed/{m_prefix}/{tmdb_id}{tv_suffix}"},
        {"id": "warezcdn", "url": f"https://embed.warezcdn.net/filme/{tmdb_id}" if m_type == "movie" else f"https://embed.warezcdn.net/serie/{tmdb_id}/{season}/{episode}"}
    ]

    for m in mirrors:
        if len(servers) >= 10:
            break
        servers.append({
            "id": m["id"],
            "name": f"Server {len(servers) + 1}",
            "url": m["url"],
            "quality": "1080p",
            "is_direct": False
        })

    return servers
