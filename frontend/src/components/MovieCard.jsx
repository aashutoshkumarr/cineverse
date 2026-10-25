import React from "react";
import { Link } from "react-router-dom";

export default function MovieCard({ item }) {
  if (!item) return null;

  const rating = parseFloat(item.rating || 7.5);
  const mediaType = item.media_type || "movie";

  // Top-Right Pill Badge text
  const getBadgeText = () => {
    if (item.badge && item.badge !== "Top Rated" && item.badge !== "Superhit" && item.badge !== "All Time Hit") {
      return item.badge;
    }
    if (item.country === "Korea") return "Korea";
    if (item.languages && item.languages.length > 0 && item.languages[0] !== "English") {
      return item.languages[0];
    }
    if (item.country && item.country !== "International" && item.country !== "Global") {
      return item.country;
    }
    return item.category || "HD";
  };

  const badgeText = getBadgeText();

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
        {/* Top-Right Pill Badge matching user screenshot */}
        {badgeText && <span className="card-top-badge">{badgeText}</span>}

        {/* Progress Bar for Continued Watching */}
        {item.progress_percent > 0 && (
          <div style={{ position: "absolute", bottom: 0, left: 0, width: "100%", height: "4px", background: "rgba(255,255,255,0.2)", zIndex: 3 }}>
            <div style={{ width: `${Math.min(item.progress_percent, 100)}%`, height: "100%", background: "#e50914" }} />
          </div>
        )}
      </div>

      {/* Overlapping Rating Circle & Year Meta Row matching user screenshot */}
      <div className="card-meta-row">
        <div className="card-rating-circle">
          {rating.toFixed(1)}
        </div>
        <span className="card-year">{item.year || "2025"}</span>
      </div>

      {/* Title */}
      <div className="card-title" title={item.title}>
        {item.title}
      </div>
    </Link>
  );
}
