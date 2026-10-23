import os
import pickle
import pandas as pd
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MOVIE_LIST_PATH = os.path.join(BASE_DIR, "movie_list.pkl")
SIMILARITY_PATH = os.path.join(BASE_DIR, "similarity.pkl")
CATALOG_PATH = os.path.join(BASE_DIR, "netmirror_catalog.json")

# Load catalog
catalog_cache = []
try:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog_cache = json.load(f)
except Exception as e:
    print("Error loading catalog:", e)

# Load ML model lazily
_ml_loaded = False
_movies_df = None
_similarity = None

def load_ml_models():
    global _ml_loaded, _movies_df, _similarity
    if _ml_loaded:
        return
    try:
        if os.path.exists(MOVIE_LIST_PATH) and os.path.exists(SIMILARITY_PATH):
            with open(MOVIE_LIST_PATH, "rb") as f:
                _movies_df = pickle.load(f)
            with open(SIMILARITY_PATH, "rb") as f:
                _similarity = pickle.load(f)
            _ml_loaded = True
            print("ML Recommender model loaded successfully!")
    except Exception as e:
        print("ML load error:", e)

def get_ml_recommendations(tmdb_id, title=None, limit=10):
    """
    Finds top similar movies using Cosine Similarity on content tags.
    Falls back gracefully to catalog similarity if not in 5k dataset.
    """
    load_ml_models()
    
    # 1. Try ML model if available
    if _ml_loaded and _movies_df is not None and _similarity is not None:
        try:
            match_row = None
            if tmdb_id:
                matches = _movies_df[_movies_df['movie_id'] == int(tmdb_id)]
                if not matches.empty:
                    match_row = matches.index[0]
            
            if match_row is None and title:
                matches = _movies_df[_movies_df['title'].str.lower() == title.lower()]
                if not matches.empty:
                    match_row = matches.index[0]
                    
            if match_row is not None:
                distances = sorted(list(enumerate(_similarity[match_row])), reverse=True, key=lambda x: x[1])
                rec_ids = [int(_movies_df.iloc[i[0]].movie_id) for i in distances[1:limit+1]]
                
                # Fetch full items from catalog if present
                rec_items = []
                for rid in rec_ids:
                    found = next((m for m in catalog_cache if int(m.get("id", 0)) == rid), None)
                    if found:
                        rec_items.append(found)
                    else:
                        m_title = str(_movies_df[_movies_df['movie_id'] == rid].iloc[0]['title'])
                        rec_items.append({
                            "id": int(rid),
                            "title": m_title,
                            "clean_title": m_title,
                            "rating": 7.8,
                            "year": "2024",
                            "badge": "ML Match",
                            "poster": f"https://image.tmdb.org/t/p/w500",
                            "category": "Recommended",
                            "country": "International"
                        })
                return rec_items
        except Exception as e:
            print("ML rec execution error:", e)

    # 2. Intelligent fallback from our 2,497 local catalog
    matched_target = next((m for m in catalog_cache if m.get("id") == tmdb_id or m.get("clean_title", "").lower() == (title or "").lower()), None)
    
    if matched_target:
        target_country = matched_target.get("country")
        target_cat = matched_target.get("category")
        target_genres = set(matched_target.get("genres", []))
        
        candidates = []
        for item in catalog_cache:
            if item.get("id") == matched_target.get("id"):
                continue
            score = 0
            if item.get("country") == target_country:
                score += 3
            if item.get("category") == target_cat:
                score += 3
            item_genres = set(item.get("genres", []))
            common = len(target_genres.intersection(item_genres))
            score += common * 2
            score += min(float(item.get("rating", 7.0)), 10.0) / 2.0
            
            candidates.append((score, item))
            
        candidates.sort(key=lambda x: -x[0])
        return [c[1] for c in candidates[:limit]]
        
    return catalog_cache[:limit]
