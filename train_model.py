"""
Cineverse ML Model Training & Artifact Generation Pipeline
==========================================================
Extracts features from TMDB 5000 datasets (genres, keywords, cast, crew, overview),
builds a unified metadata bag of words, computes the Cosine Similarity matrix,
and outputs versioned artifacts (movie_list.pkl, similarity.pkl, and model_metadata.json).

Usage:
    python train_model.py
"""

import os
import sys
import json
import ast
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MOVIES_CSV = os.path.join(BASE_DIR, "tmdb_5000_movies.csv")
CREDITS_CSV = os.path.join(BASE_DIR, "tmdb_5000_credits.csv")
OUT_MOVIE_LIST = os.path.join(BASE_DIR, "movie_list.pkl")
OUT_SIMILARITY = os.path.join(BASE_DIR, "similarity.pkl")
OUT_METADATA = os.path.join(BASE_DIR, "model_metadata.json")

def parse_features(obj, limit=None):
    """Safely extracts names from JSON strings."""
    try:
        data = ast.literal_eval(obj)
        names = [item['name'].replace(" ", "").lower() for item in data if isinstance(item, dict) and 'name' in item]
        return names[:limit] if limit else names
    except Exception:
        return []

def get_director(crew_obj):
    """Extracts director from crew JSON string."""
    try:
        data = ast.literal_eval(crew_obj)
        for item in data:
            if isinstance(item, dict) and item.get('job') == 'Director':
                return [item['name'].replace(" ", "").lower()]
        return []
    except Exception:
        return []

def train():
    print("=" * 60)
    print("🚀 Cineverse ML Training Pipeline Starting...")
    print("=" * 60)

    if not os.path.exists(MOVIES_CSV) or not os.path.exists(CREDITS_CSV):
        print(f"❌ Error: Missing datasets ({MOVIES_CSV} or {CREDITS_CSV})")
        sys.exit(1)

    print("[1/5] Loading TMDB 5000 Movies & Credits datasets...")
    movies = pd.read_csv(MOVIES_CSV)
    credits = pd.read_csv(CREDITS_CSV)

    print(f"      Loaded {len(movies)} movies and {len(credits)} credits records.")

    print("[2/5] Merging datasets on title...")
    df = movies.merge(credits, on="title")

    # Keep necessary feature columns
    # id, title, overview, genres, keywords, cast, crew
    df = df[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']].dropna()

    print("[3/5] Extracting & cleaning metadata features...")
    df['genres'] = df['genres'].apply(parse_features)
    df['keywords'] = df['keywords'].apply(parse_features)
    df['cast'] = df['cast'].apply(lambda x: parse_features(x, limit=3))
    df['director'] = df['crew'].apply(get_director)
    df['overview'] = df['overview'].apply(lambda x: [w.lower() for w in str(x).split()])

    # Combine all tags
    df['tags'] = df['overview'] + df['genres'] + df['keywords'] + df['cast'] + df['director']
    df['tags_string'] = df['tags'].apply(lambda x: " ".join(x))

    new_df = df[['movie_id', 'title', 'tags_string', 'tags']].copy()
    new_df.rename(columns={'tags_string': 'tags_text'}, inplace=True)

    print("[4/5] Vectorizing text & computing Cosine Similarity matrix...")
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors = cv.fit_transform(new_df['tags_text']).toarray()
    print(f"      Vocabulary size: {vectors.shape[1]} features across {vectors.shape[0]} titles.")

    similarity = cosine_similarity(vectors)
    print(f"      Similarity matrix shape: {similarity.shape}")

    print("[5/5] Saving model artifacts & metadata...")
    with open(OUT_MOVIE_LIST, "wb") as f:
        pickle.dump(new_df[['movie_id', 'title', 'tags']], f)
    
    with open(OUT_SIMILARITY, "wb") as f:
        pickle.dump(similarity, f)

    meta = {
        "model_name": "Cineverse Content-Based Cosine Similarity Recommender",
        "version": "2.0.0",
        "trained_at": datetime.now().isoformat(),
        "total_titles": int(len(new_df)),
        "feature_count": int(vectors.shape[1]),
        "similarity_matrix_dimensions": list(similarity.shape),
        "source_dataset": "TMDB 5000 Movie Dataset",
        "algorithm": "CountVectorizer + Cosine Similarity",
        "status": "ready"
    }
    with open(OUT_METADATA, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"✅ Training Complete! Artifacts written:")
    print(f"   • {OUT_MOVIE_LIST} ({os.path.getsize(OUT_MOVIE_LIST):,} bytes)")
    print(f"   • {OUT_SIMILARITY} ({os.path.getsize(OUT_SIMILARITY):,} bytes)")
    print(f"   • {OUT_METADATA}")
    print("=" * 60)

if __name__ == "__main__":
    train()
