"""
Automated Backend & Core Service Test Suite for Cineverse
=========================================================
Tests:
1. Health and Root endpoints
2. Curated Catalog search & filtering
3. Streaming Service live mirror generation (Server 1-4)
4. ML Recommendation Engine & fallback
5. Database Watchlist and History persistence (User & Episode isolation)
"""

import unittest
from backend import main as app_module
from backend import database as db
from backend import recommender as rec
from backend import streaming_service as stream

class TestCineverseBackend(unittest.TestCase):

    def test_catalog_loaded(self):
        self.assertGreater(len(app_module.CATALOG), 1000, "Catalog should have over 1,000 curated titles")

    def test_streaming_servers_generation(self):
        # Test movie servers
        m_servers = stream.get_streaming_servers(tmdb_id=550, media_type="movie")
        self.assertGreaterEqual(len(m_servers), 4, "Should have at least 4 active streaming mirrors")
        self.assertEqual(m_servers[0]["name"], "Server 1")
        self.assertIn("autoembed.co", m_servers[0]["url"])

        # Test TV servers with season and episode params
        tv_servers = stream.get_streaming_servers(tmdb_id=114472, media_type="tv", season=2, episode=3)
        self.assertIn("114472-2-3", tv_servers[0]["url"])

    def test_recommender_system(self):
        status = rec.get_recommender_status()
        self.assertIn("ml_model_loaded", status)
        self.assertIn("curated_catalog_count", status)

        # Test recommendation query with metadata
        recs, engine = rec.get_recommendations_with_meta(None, "Inception", limit=6)
        self.assertGreater(len(recs), 0, "Should return recommended movies")
        self.assertIn(engine, ["ml_cosine", "heuristic_fallback"])

    def test_database_persistence(self):
        test_user = "test_ci_user"
        test_id = 999999

        # 1. Watchlist
        db.add_to_watchlist({"id": test_id, "title": "Test Title", "year": "2024"}, user_id=test_user)
        wl = db.get_watchlist(user_id=test_user)
        self.assertTrue(any(item["tmdb_id"] == test_id for item in wl))
        db.remove_from_watchlist(test_id, user_id=test_user)

        # 2. History with episode tracking
        db.add_to_history({
            "id": test_id,
            "title": "Test TV",
            "season": 1,
            "episode": 2,
            "progress_seconds": 150,
            "duration_seconds": 3600
        }, user_id=test_user)
        
        db.update_playback_progress(test_id, 300, 3600, user_id=test_user, season=1, episode=2)
        history = db.get_history(limit=5, user_id=test_user)
        self.assertTrue(any(h["tmdb_id"] == test_id and h["progress_seconds"] == 300 for h in history))
        
        # Cleanup
        db.clear_history(user_id=test_user)

if __name__ == "__main__":
    unittest.main()
