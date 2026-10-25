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

def get_ml_recommendations(tmdb_id, title=None, limit=12):
    """
    Finds top similar movies using Cosine Similarity on content tags,
    prioritizing movies that have authentic posters in our catalog.
    Falls back seamlessly to intelligent genre/country/keyword matching from local 2,500 catalog.
    Never returns generic fallback posters or missing posters.
    """
    load_ml_models()
    
    rec_items = []
    seen_ids = set()
    if tmdb_id:
        try:
            seen_ids.add(int(tmdb_id))
        except (ValueError, TypeError):
            pass

    cat_by_id = {int(m.get("id", 0)): m for m in catalog_cache if m.get("id")}
    cat_by_clean = {str(m.get("clean_title", "")).strip().lower(): m for m in catalog_cache if m.get("clean_title")}
    cat_by_title = {str(m.get("title", "")).strip().lower(): m for m in catalog_cache if m.get("title")}

    # 1. Try ML model if available and map directly to full catalog items
    if _ml_loaded and _movies_df is not None and _similarity is not None:
        try:
            match_row = None
            if tmdb_id:
                try:
                    matches = _movies_df[_movies_df['movie_id'] == int(tmdb_id)]
                    if not matches.empty:
                        match_row = matches.index[0]
                except (ValueError, TypeError):
                    pass
            
            if match_row is None and title:
                matches = _movies_df[_movies_df['title'].str.lower() == str(title).strip().lower()]
                if not matches.empty:
                    match_row = matches.index[0]
                    
            if match_row is not None:
                distances = sorted(list(enumerate(_similarity[match_row])), reverse=True, key=lambda x: x[1])
                for idx, dist in distances[1:]:
                    mid = int(_movies_df.iloc[idx]['movie_id'])
                    mtitle = str(_movies_df.iloc[idx]['title']).strip().lower()
                    
                    found = cat_by_id.get(mid) or cat_by_clean.get(mtitle) or cat_by_title.get(mtitle)
                    if found and found.get("id") not in seen_ids:
                        poster = found.get("poster", "")
                        if poster and "unsplash" not in poster:
                            rec_items.append(found)
                            seen_ids.add(found.get("id"))
                            if len(rec_items) >= limit:
                                break
        except Exception as e:
            print("ML rec execution error:", e)

    # 2. Intelligent fallback from our 2,500+ local verified catalog
    if len(rec_items) < limit:
        matched_target = None
        if tmdb_id:
            matched_target = next((m for m in catalog_cache if str(m.get("id")) == str(tmdb_id)), None)
        if not matched_target and title:
            t_lower = str(title).strip().lower()
            matched_target = next((m for m in catalog_cache if m.get("clean_title", "").lower() == t_lower or m.get("title", "").lower() == t_lower), None)
            if not matched_target:
                matched_target = next((m for m in catalog_cache if t_lower in m.get("clean_title", "").lower()), None)
        
        target_country = matched_target.get("country") if matched_target else None
        target_cat = matched_target.get("category") if matched_target else None
        target_genres = set(matched_target.get("genres", [])) if matched_target else set()
        target_keywords = set(str(matched_target.get("clean_title", "")).lower().split()) if matched_target else set()

        candidates = []
        for item in catalog_cache:
            iid = item.get("id")
            if iid in seen_ids:
                continue
            poster = item.get("poster", "")
            if not poster or "unsplash" in poster:
                continue
                
            score = 0
            if target_country and item.get("country") == target_country:
                score += 4
            if target_cat and item.get("category") == target_cat:
                score += 3
            item_genres = set(item.get("genres", []))
            common = len(target_genres.intersection(item_genres))
            score += common * 3
            
            item_keywords = set(str(item.get("clean_title", "")).lower().split())
            common_kw = len(target_keywords.intersection(item_keywords))
            score += common_kw * 2
            
            score += min(float(item.get("rating", 7.0)), 10.0) / 2.0
            candidates.append((score, item))
            
        candidates.sort(key=lambda x: -x[0])
        for _, c_item in candidates:
            rec_items.append(c_item)
            seen_ids.add(c_item.get("id"))
            if len(rec_items) >= limit:
                break

    return rec_items if rec_items else catalog_cache[:limit]
