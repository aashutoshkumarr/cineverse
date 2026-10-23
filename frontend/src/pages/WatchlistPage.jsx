import React, { useState, useEffect } from "react";
import { fetchWatchlist, removeFromWatchlist } from "../services/api";
import { Link } from "react-router-dom";
import { Bookmark, Trash2, Play } from "lucide-react";

export default function WatchlistPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWatchlist();
  }, []);

  const loadWatchlist = () => {
    setLoading(true);
    fetchWatchlist()
      .then((data) => setItems(data))
      .finally(() => setLoading(false));
  };

  const handleRemove = async (e, tmdbId) => {
    e.preventDefault();
    e.stopPropagation();
    await removeFromWatchlist(tmdbId);
    setItems((prev) => prev.filter((i) => (i.tmdb_id !== tmdbId && i.id !== tmdbId)));
  };

  return (
    <div className="container" style={{ paddingTop: "30px", paddingBottom: "60px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "25px" }}>
        <h1 style={{ fontSize: "28px", fontWeight: "900", display: "flex", alignItems: "center", gap: "10px" }}>
          <Bookmark color="#38bdf8" />
          <span>Your Personal Watchlist</span>
          <span className="badge-counter">{items.length} Titles</span>
        </h1>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: "60px", color: "#94a3b8" }}>
          Loading watchlist...
        </div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: "center", padding: "80px 20px", background: "rgba(255,255,255,0.02)", borderRadius: "16px" }}>
          <h3 style={{ fontSize: "20px", marginBottom: "8px" }}>Your Watchlist is empty</h3>
          <p style={{ color: "#94a3b8", marginBottom: "20px" }}>Browse movies and click "Add to Watchlist" to save them here.</p>
          <Link to="/" className="btn-primary">
            Explore Movies
          </Link>
        </div>
      ) : (
        <div className="movie-grid">
          {items.map((item) => {
            const mId = item.tmdb_id || item.id;
            return (
              <div key={mId} style={{ position: "relative" }}>
                <Link to={`/watch/${mId}?type=${item.media_type || 'movie'}`} className="movie-card" style={{ height: "100%" }}>
                  <div className="poster-wrap">
                    <img src={item.poster} alt={item.title} className="poster-img" />
                    <span className="card-badge">{item.media_type?.toUpperCase() || "HD"}</span>
                    <div className="card-rating">
                      {parseFloat(item.rating || 7.5).toFixed(1)}
                    </div>
                  </div>
                  <div className="card-body">
                    <div className="card-title">{item.title}</div>
                    <div className="card-meta">
                      <span>{item.year}</span>
                    </div>
                  </div>
                </Link>

                <button
                  onClick={(e) => handleRemove(e, mId)}
                  title="Remove from Watchlist"
                  style={{
                    position: "absolute",
                    top: "8px",
                    right: "8px",
                    background: "rgba(239, 68, 68, 0.85)",
                    border: "none",
                    borderRadius: "6px",
                    color: "#ffffff",
                    width: "30px",
                    height: "30px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: "pointer",
                    zIndex: 10
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
