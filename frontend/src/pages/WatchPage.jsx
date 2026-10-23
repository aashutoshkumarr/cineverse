import React, { useState, useEffect, useRef } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import { fetchMovieDetail, addToWatchlist, addToHistory, updatePlaybackProgress } from "../services/api";
import MovieCard from "../components/MovieCard";
import TrailerPlayer from "../components/TrailerPlayer";
import VideoPlayer from "../components/VideoPlayer";
import { Play, Bookmark, Star, Tv, ArrowLeft, ChevronLeft, ChevronRight, Check, Zap, Globe } from "lucide-react";

export default function WatchPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const mediaType = searchParams.get("type") || "movie";

  const [season, setSeason] = useState(1);
  const [episode, setEpisode] = useState(1);
  const [activeServer, setActiveServer] = useState(0);
  const [playerMode, setPlayerMode] = useState("cdn"); // "cdn" or "servers"
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [added, setAdded] = useState(false);
  const [showPlayer, setShowPlayer] = useState(false);

  const playerRef = useRef(null);
  const similarRef = useRef(null);

  useEffect(() => {
    setLoading(true);
    fetchMovieDetail(id, mediaType, season, episode)
      .then((data) => {
        setDetail(data);
        setActiveServer(0);
        if (data.direct_stream) {
          setPlayerMode("cdn");
        } else {
          setPlayerMode("servers");
        }

        // Record in history automatically
        if (data.item) {
          addToHistory({
            id: data.item.id,
            title: data.item.title,
            poster: data.item.poster,
            year: data.item.year,
            rating: data.item.rating,
            media_type: mediaType,
            progress_seconds: data.resume_seconds || 0,
            duration_seconds: data.duration_seconds || 0
          }).catch(() => {});
        }
      })
      .finally(() => setLoading(false));
  }, [id, mediaType, season, episode]);

  const handleWatchFreeClick = () => {
    setShowPlayer(true);
    setTimeout(() => {
      if (playerRef.current) {
        playerRef.current.scrollIntoView({ behavior: "smooth" });
      }
    }, 100);
  };

  const handleWatchlist = async () => {
    if (!detail || !detail.item) return;
    try {
      await addToWatchlist({
        id: detail.item.id,
        title: detail.item.title,
        poster: detail.item.poster,
        year: detail.item.year,
        rating: detail.item.rating,
        media_type: mediaType
      });
      setAdded(true);
      setTimeout(() => setAdded(false), 2500);
    } catch (err) {
      console.error(err);
    }
  };

  const scrollSimilar = (direction) => {
    if (similarRef.current) {
      const scrollAmount = 500;
      similarRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth"
      });
    }
  };

  if (loading) {
    return (
      <div className="container" style={{ textAlign: "center", padding: "120px 0" }}>
        <h2 style={{ color: "#94a3b8" }}>Loading movie details...</h2>
      </div>
    );
  }

  if (!detail || !detail.item) {
    return (
      <div className="container" style={{ textAlign: "center", padding: "100px 0" }}>
        <h2>Title not found</h2>
        <Link to="/" className="btn-primary" style={{ marginTop: "20px" }}>
          Back to Home
        </Link>
      </div>
    );
  }

  const { item, streaming_servers = [], trailer, cast = [], genres = [], recommendations = [] } = detail;
  const ratingVal = parseFloat(item.rating || 7.5);
  const currentEmbedUrl = streaming_servers[activeServer]?.url || streaming_servers[0]?.url;

  return (
    <div className="container" style={{ paddingTop: "24px", paddingBottom: "80px" }}>
      {/* 1. Breadcrumbs */}
      <div style={{ fontSize: "14px", color: "#64748b", marginBottom: "24px", display: "flex", alignItems: "center", gap: "8px" }}>
        <Link to="/" style={{ color: "#38bdf8", textDecoration: "none" }}>Home</Link>
        <span>&gt;</span>
        <span style={{ color: "#94a3b8" }}>{item.title}</span>
      </div>

      {/* 2. Hero Detail Header (NetMirror Exact Layout) */}
      <div style={{ display: "flex", gap: "32px", marginBottom: "36px", flexWrap: "wrap", alignItems: "flex-start" }}>
        {/* Left Poster */}
        <div style={{ width: "200px", flexShrink: 0 }}>
          <img
            src={item.poster}
            alt={item.title}
            style={{
              width: "100%",
              borderRadius: "14px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.7)",
              border: "1px solid rgba(255,255,255,0.1)",
              objectFit: "cover",
              aspectRatio: "2 / 3"
            }}
          />
        </div>

        {/* Right Info */}
        <div style={{ flex: 1, minWidth: "300px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "20px", flexWrap: "wrap", marginBottom: "14px" }}>
            <h1 style={{ fontSize: "36px", fontWeight: "900", color: "#ffffff", margin: 0, letterSpacing: "-0.5px" }}>
              {item.title}
            </h1>

            {/* Watch Free Button (Bright NetMirror Style) */}
            <button
              onClick={handleWatchFreeClick}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                background: "linear-gradient(135deg, #f97316 0%, #eab308 100%)",
                color: "#000000",
                fontWeight: "900",
                fontSize: "15px",
                padding: "10px 22px",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
                boxShadow: "0 4px 16px rgba(249, 115, 22, 0.4)",
                transition: "transform 0.15s"
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = "scale(1.04)"}
              onMouseLeave={(e) => e.currentTarget.style.transform = "scale(1)"}
            >
              <span style={{ color: "#dc2626", fontSize: "14px" }}>▶</span>
              <span>Watch Free</span>
            </button>
          </div>

          {/* Genre Badges (Red/Pink Pills) */}
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
            {genres.map((g, idx) => (
              <span
                key={idx}
                style={{
                  background: "#e11d48",
                  color: "#ffffff",
                  fontSize: "12px",
                  fontWeight: "700",
                  padding: "3px 12px",
                  borderRadius: "6px"
                }}
              >
                {g}
              </span>
            ))}
          </div>

          {/* Rating with Green Circle Ring */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px", fontSize: "15px" }}>
            <span style={{ color: "#94a3b8", fontWeight: "600" }}>Rating :</span>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                border: "2.5px solid #00e676",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#ffffff",
                fontWeight: "800",
                fontSize: "13px",
                background: "#041226"
              }}
            >
              {ratingVal.toFixed(1)}
            </div>
          </div>

          {/* Country */}
          <div style={{ fontSize: "15px", color: "#cbd5e1", marginBottom: "8px" }}>
            <span style={{ color: "#94a3b8", fontWeight: "600" }}>Country: </span>
            <span>{item.country || "Korea"}</span>
          </div>

          {/* Release Date */}
          <div style={{ fontSize: "15px", color: "#cbd5e1", marginBottom: "20px" }}>
            <span style={{ color: "#94a3b8", fontWeight: "600" }}>Release Date: </span>
            <span>{item.release_date || item.year}</span>
          </div>

          {/* Watchlist Action */}
          <button
            onClick={handleWatchlist}
            className="btn-secondary"
            style={{ fontSize: "13px", padding: "8px 16px" }}
          >
            {added ? <Check size={16} color="#00e676" /> : <Bookmark size={16} />}
            <span>{added ? "Saved to Watchlist" : "Add to Watchlist"}</span>
          </button>
        </div>
      </div>

      {/* 3. About Section */}
      <div style={{ marginBottom: "36px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "20px" }}>
        <p style={{ fontSize: "15px", color: "#cbd5e1", lineHeight: "1.7" }}>
          <b style={{ color: "#ffffff" }}>About: </b>
          "{item.overview || 'A gripping and entertaining title with incredible performances and story.'}"
        </p>
      </div>

      {/* 4. Cinema Streaming Player (Native CDN Player or 10 Servers) */}
      {showPlayer && (
        <div ref={playerRef} style={{ marginBottom: "50px", scrollMarginTop: "90px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
              <h2 style={{ fontSize: "20px", fontWeight: "800", color: "#ffffff", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
                <span style={{ color: "#f97316" }}>▶</span> Full Cinema Player
              </h2>

              {/* Source Mode Switcher (Step 5: Managed CDN HLS vs Multi-Server) */}
              {detail.direct_stream && (
                <div style={{ display: "flex", gap: "6px", background: "rgba(255,255,255,0.06)", padding: "3px", borderRadius: "8px" }}>
                  <button
                    onClick={() => setPlayerMode("cdn")}
                    style={{
                      background: playerMode === "cdn" ? "#0284c7" : "transparent",
                      color: playerMode === "cdn" ? "#ffffff" : "#94a3b8",
                      border: "none",
                      padding: "4px 12px",
                      borderRadius: "6px",
                      fontSize: "12px",
                      fontWeight: "700",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "5px"
                    }}
                  >
                    <Zap size={13} /> Native CDN (HLS)
                  </button>
                  <button
                    onClick={() => setPlayerMode("servers")}
                    style={{
                      background: playerMode === "servers" ? "#f97316" : "transparent",
                      color: playerMode === "servers" ? "#ffffff" : "#94a3b8",
                      border: "none",
                      padding: "4px 12px",
                      borderRadius: "6px",
                      fontSize: "12px",
                      fontWeight: "700",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "5px"
                    }}
                  >
                    <Globe size={13} /> 10 Servers
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={() => setShowPlayer(false)}
              style={{ background: "none", border: "none", color: "#94a3b8", fontSize: "13px", cursor: "pointer" }}
            >
              ✕ Close Player
            </button>
          </div>

          {/* Conditional Player View */}
          {playerMode === "cdn" && detail.direct_stream ? (
            <div style={{ marginBottom: "20px" }}>
              <VideoPlayer
                src={detail.direct_stream.playback_url}
                type={detail.direct_stream.playback_type}
                initialTime={detail.resume_seconds || 0}
                poster={item.poster}
                title={item.title}
                onProgress={(curr, dur) => {
                  updatePlaybackProgress(item.id, curr, dur);
                }}
              />

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", background: "#081a36", borderRadius: "8px", marginTop: "10px", fontSize: "13px", color: "#94a3b8" }}>
                <span style={{ color: "#38bdf8", fontWeight: "600", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Zap size={14} /> High-Speed Video.js HLS Delivery Active (Adaptive 1080p · Zero Buffering)
                </span>
                {detail.resume_seconds > 10 && (
                  <span style={{ color: "#00e676", fontWeight: "600" }}>
                    🕒 Resumed from {Math.floor(detail.resume_seconds / 60)}m {Math.floor(detail.resume_seconds % 60)}s
                  </span>
                )}
              </div>
            </div>
          ) : (
            /* Video Player Container for 10 Embed Servers */
            <div className="player-container">
              <div className="video-frame-wrap">
                <iframe
                  key={`${currentEmbedUrl}-${activeServer}`}
                  src={currentEmbedUrl}
                  title={item.title}
                  className="video-frame"
                  referrerPolicy="no-referrer"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; fullscreen"
                  allowFullScreen
                />
              </div>

              {/* Clean Server Switcher Bar (Exact match with screenshot 2) */}
              <div className="server-bar">
                <div className="server-list" style={{ display: "flex", alignItems: "center", width: "100%", flexWrap: "wrap", gap: "8px" }}>
                  {streaming_servers.map((srv, idx) => (
                    <button
                      key={srv.id}
                      className={`server-btn ${activeServer === idx ? "active" : ""}`}
                      onClick={() => setActiveServer(idx)}
                    >
                      {activeServer === idx ? `📶 Server ${idx + 1}` : `Server ${idx + 1}`}
                    </button>
                  ))}

                  {currentEmbedUrl && (
                    <a
                      href={currentEmbedUrl}
                      target="_blank"
                      rel="noreferrer noopener"
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                        background: "rgba(255,255,255,0.06)",
                        border: "1px solid rgba(255,255,255,0.15)",
                        color: "#94a3b8",
                        padding: "6px 14px",
                        borderRadius: "6px",
                        fontSize: "12px",
                        textDecoration: "none",
                        fontWeight: "600",
                        marginLeft: "auto",
                        transition: "all 0.15s"
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = "#ffffff"; e.currentTarget.style.borderColor = "#38bdf8"; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = "#94a3b8"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.15)"; }}
                      title="Open video in a new full window tab if blocked by browser or ISP"
                    >
                      <span>↗ Open Tab</span>
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TV Series Controls */}
          {mediaType === "tv" && (
            <div style={{ background: "#081a36", padding: "16px 20px", borderRadius: "12px", marginBottom: "20px", border: "1px solid rgba(255,255,255,0.08)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap", marginBottom: "12px" }}>
                <span style={{ fontWeight: "700", fontSize: "13px", color: "#38bdf8", display: "flex", alignItems: "center", gap: "6px" }}>
                  <Tv size={16} /> Select Season:
                </span>
                {[1, 2, 3, 4, 5].map((s) => (
                  <button
                    key={s}
                    className={`filter-pill ${season === s ? "active" : ""}`}
                    onClick={() => { setSeason(s); setEpisode(1); }}
                  >
                    Season {s}
                  </button>
                ))}
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <span style={{ fontWeight: "700", fontSize: "13px", color: "#94a3b8" }}>Episode:</span>
                {Array.from({ length: 12 }, (_, i) => i + 1).map((ep) => (
                  <button
                    key={ep}
                    className={`server-btn ${episode === ep ? "active" : ""}`}
                    style={{ padding: "4px 10px", fontSize: "12px" }}
                    onClick={() => setEpisode(ep)}
                  >
                    Ep {ep}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 5. Clean Cinema Trailer Section (No YouTube Branding / Watermarks) */}
      <TrailerPlayer trailer={trailer} poster={item.poster} title={item.title} />

      {/* 6. Starring Section (Circular Avatars - Screenshot 2 Exact) */}
      {cast.length > 0 && (
        <div style={{ marginBottom: "48px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "24px" }}>
          <h2 style={{ fontSize: "20px", fontWeight: "800", color: "#ffffff", marginBottom: "20px" }}>
            Starring
          </h2>
          <div style={{ display: "flex", gap: "32px", overflowX: "auto", paddingBottom: "12px" }}>
            {cast.map((actor, idx) => (
              <div key={idx} style={{ textAlign: "center", width: "110px", flexShrink: 0 }}>
                <img
                  src={actor.photo || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&q=80"}
                  alt={actor.name}
                  style={{
                    width: "90px",
                    height: "90px",
                    borderRadius: "50%",
                    objectFit: "cover",
                    marginBottom: "10px",
                    border: "2px solid rgba(255,255,255,0.15)",
                    background: "#081a36"
                  }}
                  onError={(e) => {
                    e.target.src = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&q=80";
                  }}
                />
                <div style={{ fontSize: "14px", fontWeight: "700", color: "#ffffff", lineHeight: "1.2", marginBottom: "4px" }}>
                  {actor.name}
                </div>
                <div style={{ fontSize: "12px", color: "#94a3b8" }}>
                  {actor.character}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. Similar Title Carousel (Screenshot 2 Exact) */}
      {recommendations.length > 0 && (
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "24px", position: "relative" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
            <h2 style={{ fontSize: "20px", fontWeight: "800", color: "#ffffff" }}>
              Similar Title
            </h2>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                onClick={() => scrollSimilar("left")}
                className="scroll-arrow"
                style={{ position: "static", transform: "none", width: "34px", height: "34px" }}
              >
                <ChevronLeft size={18} />
              </button>
              <button
                onClick={() => scrollSimilar("right")}
                className="scroll-arrow"
                style={{ position: "static", transform: "none", width: "34px", height: "34px" }}
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>

          <div className="shelf-scroll-row" ref={similarRef}>
            {recommendations.map((rec) => (
              <MovieCard key={rec.id} item={rec} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
