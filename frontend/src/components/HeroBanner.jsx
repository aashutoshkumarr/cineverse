import React from "react";
import { Link } from "react-router-dom";
import { Play, Info, Star } from "lucide-react";

export default function HeroBanner({ movie }) {
  if (!movie) return null;

  const bgImage = movie.poster;

  return (
    <div
      className="hero-banner"
      style={{
        backgroundImage: `url(${bgImage})`
      }}
    >
      <div className="hero-overlay" />
      <div className="hero-content">
        <span className="hero-tag">🔥 Featured Blockbuster</span>
        <h1 className="hero-title">{movie.title}</h1>
        <div className="hero-meta">
          <span style={{ display: "flex", alignItems: "center", gap: "4px", color: "#facc15", fontWeight: "700" }}>
            <Star size={16} fill="#facc15" /> {movie.rating}/10
          </span>
          <span>•</span>
          <span>{movie.year}</span>
          <span>•</span>
          <span>{movie.country}</span>
          <span>•</span>
          <span style={{ color: "#00e676", fontWeight: "600" }}>Ultra HD 4K</span>
        </div>
        <p className="hero-desc">{movie.overview}</p>
        <div className="hero-buttons">
          <Link to={`/watch/${movie.id}?type=${movie.media_type || 'movie'}&watch=1`} className="btn-primary">
            <Play size={18} fill="#ffffff" /> Watch Now
          </Link>
          <Link to={`/watch/${movie.id}?type=${movie.media_type || 'movie'}`} className="btn-secondary">
            <Info size={18} /> Details & Trailer
          </Link>
        </div>
      </div>
    </div>
  );
}
