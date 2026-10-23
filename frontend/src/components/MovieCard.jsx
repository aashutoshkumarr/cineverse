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
      </div>
      <div className="card-body">
        <div className="card-title" title={item.title}>
          {item.title}
        </div>
        <div className="card-meta">
          <span>{item.year || "2024"}</span>
          <span>{item.country || "Global"}</span>
        </div>
      </div>
    </Link>
  );
}
