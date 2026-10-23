import React from "react";
import { Link } from "react-router-dom";
import { Play } from "lucide-react";

export default function MovieCard({ item }) {
  if (!item) return null;

  const rating = parseFloat(item.rating || 7.5);
  const ratingClass = rating >= 7.8 ? "" : (rating >= 6.5 ? "yellow" : "orange");
  const mediaType = item.media_type || "movie";

  return (
    <Link to={`/watch/${item.id}?type=${mediaType}`} className="movie-card">
      <div className="poster-wrap">
        <img
          src={item.poster}
          alt={item.title}
          className="poster-img"
          loading="lazy"
          onError={(e) => {
            e.target.src = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&q=80";
          }}
        />
        <span className="card-badge">{item.badge || item.category || "HD"}</span>
        <div className={`card-rating ${ratingClass}`}>
          {rating.toFixed(1)}
        </div>
        {item.progress_percent > 0 && (
          <div style={{ position: "absolute", bottom: 0, left: 0, width: "100%", height: "4px", background: "rgba(255,255,255,0.2)", zIndex: 3 }}>
            <div style={{ width: `${Math.min(item.progress_percent, 100)}%`, height: "100%", background: "#e50914" }} />
          </div>
        )}
      </div>
      <div className="card-body">
        <div className="card-title" title={item.title}>
          {item.title}
        </div>
        <div className="card-meta">
          <span>{item.year || "2024"}</span>
          {item.progress_percent > 0 ? (
            <span style={{ color: "#38bdf8", fontWeight: "700" }}>Resume {Math.round(item.progress_percent)}%</span>
          ) : (
            <span>{item.country || "Global"}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
