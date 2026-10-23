import React, { useState, useEffect } from "react";
import { fetchHistory, clearHistory } from "../services/api";
import { Link } from "react-router-dom";
import { Clock, Trash2, ArrowLeft } from "lucide-react";
import MovieCard from "../components/MovieCard";

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory()
      .then((data) => setItems(data))
      .finally(() => setLoading(false));
  }, []);

  const handleClear = async () => {
    await clearHistory();
    setItems([]);
  };

  return (
    <div className="container" style={{ paddingTop: "30px", paddingBottom: "60px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "25px" }}>
        <h1 style={{ fontSize: "28px", fontWeight: "900", display: "flex", alignItems: "center", gap: "10px" }}>
          <Clock color="#00e676" />
          <span>Recently Watched & Played</span>
          <span className="badge-counter">{items.length} Titles</span>
        </h1>

        {items.length > 0 && (
          <button
            onClick={handleClear}
            className="btn-secondary"
            style={{ color: "#ef4444", borderColor: "rgba(239, 68, 68, 0.3)" }}
          >
            <Trash2 size={16} /> Clear History
          </button>
        )}
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: "60px", color: "#94a3b8" }}>
          Loading history...
        </div>
      ) : items.length === 0 ? (
        <div style={{ textAlign: "center", padding: "80px 20px", background: "rgba(255,255,255,0.02)", borderRadius: "16px" }}>
          <h3 style={{ fontSize: "20px", marginBottom: "8px" }}>No watch history yet</h3>
          <p style={{ color: "#94a3b8", marginBottom: "20px" }}>Titles you play in Cinema mode will automatically appear here.</p>
          <Link to="/" className="btn-primary">
            Start Watching
          </Link>
        </div>
      ) : (
        <div className="movie-grid">
          {items.map((item) => {
            const progPercent = (item.progress_seconds && item.duration_seconds && item.duration_seconds > 0)
              ? (item.progress_seconds / item.duration_seconds) * 100
              : 0;
            return (
              <MovieCard
                key={item.tmdb_id || item.id}
                item={{
                  ...item,
                  id: item.tmdb_id || item.id,
                  progress_percent: progPercent
                }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
