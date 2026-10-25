import React, { useState, useEffect, useRef } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import { fetchMovieDetail, addToWatchlist, addToHistory, updatePlaybackProgress } from "../services/api";
import MovieCard from "../components/MovieCard";
import TrailerPlayer from "../components/TrailerPlayer";
import VideoPlayer from "../components/VideoPlayer";
import { Play, Bookmark, Star, Tv, ArrowLeft, ChevronLeft, ChevronRight, Check, Zap, Globe } from "lucide-react";

export default function WatchPage() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const mediaTypeParam = searchParams.get("type");

  const [season, setSeason] = useState(1);
  const [episode, setEpisode] = useState(1);
  
  const getInitialServer = () => {
    try {
      const saved = localStorage.getItem("cineverse_preferred_server");
      if (saved !== null) {
        const idx = parseInt(saved, 10);
        if (!isNaN(idx) && idx >= 0 && idx < 10) return idx;
      }
    } catch (_) {}
    return 0;
  };

  const [activeServer, setActiveServer] = useState(getInitialServer);
  const [iframeLoading, setIframeLoading] = useState(true);
  const [showSlowWarning, setShowSlowWarning] = useState(false);
  const [playerMode, setPlayerMode] = useState("servers"); // Default to 10 Servers
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [added, setAdded] = useState(false);
  const shouldAutoWatch = searchParams.get("watch") === "1" || searchParams.get("play") === "true";
  const [isWatchMode, setIsWatchMode] = useState(shouldAutoWatch);
  const [isPlaying, setIsPlaying] = useState(shouldAutoWatch);

  const playerRef = useRef(null);
  const similarRef = useRef(null);

  useEffect(() => {
    setIframeLoading(true);
    setShowSlowWarning(false);
    const timer = setTimeout(() => {
      setShowSlowWarning(true);
    }, 5500);
    return () => clearTimeout(timer);
  }, [activeServer, season, episode, id]);

  const handleServerSelect = (idx) => {
    setActiveServer(idx);
    setIsPlaying(true);
    setIframeLoading(true);
    try {
      localStorage.setItem("cineverse_preferred_server", idx.toString());
    } catch (_) {}
  };

  useEffect(() => {
    const watchFlag = searchParams.get("watch") === "1" || searchParams.get("play") === "true";
    setIsWatchMode(watchFlag);
    if (watchFlag) setIsPlaying(true);
  }, [searchParams]);

  useEffect(() => {
    setLoading(true);
    fetchMovieDetail(id, mediaTypeParam, season, episode)
      .then((data) => {
        setDetail(data);
        setPlayerMode("servers");

        // Record in history automatically
        if (data.item) {
          addToHistory({
            id: data.item.id,
            title: data.item.title,
            poster: data.item.poster,
            year: data.item.year,
            rating: data.item.rating,
            media_type: data.media_type || data.item.media_type || "movie",
            progress_seconds: data.resume_seconds || 0,
            duration_seconds: data.duration_seconds || 0
          }).catch(() => {});
        }
      })
      .finally(() => setLoading(false));
  }, [id, mediaTypeParam, season, episode]);

  const handleWatchFreeClick = () => {
    setIsWatchMode(true);
    setIsPlaying(true);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      p.set("watch", "1");
      return p;
    });
    window.scrollTo({ top: 0, behavior: "instant" });
  };

  const handleBackToDetails = () => {
    setIsWatchMode(false);
    setIsPlaying(false);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      p.delete("watch");
      return p;
    });
    window.scrollTo({ top: 0, behavior: "instant" });
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

  const { item, streaming_servers = [], direct_stream, trailer, cast = [], genres = [], recommendations = [], seasons = [], media_type, episodes_info = [], current_thumbnail, resume_seconds = 0 } = detail || {};
  const ratingVal = parseFloat(item?.rating || 7.5);
  const currentEmbedUrl = streaming_servers[activeServer]?.url || streaming_servers[0]?.url || "";
  const directStreamUrl = direct_stream?.playback_url || null;

  // Grounded media type and TV series status
  const effectiveMediaType = media_type || item?.media_type || mediaTypeParam || "movie";
  const isTvSeries = effectiveMediaType === "tv" || (seasons && seasons.length > 0);
  const effectiveSeasons = (seasons && seasons.length > 0) ? seasons : (isTvSeries ? [{ season: 1, episodes: 8, name: "Season 1" }] : []);

  // Grounded Season & Episode mapping with authentic season posters and episode stills
  const activeSeasonObj = (effectiveSeasons && effectiveSeasons.length > 0) ? (effectiveSeasons.find((s) => s.season === season) || effectiveSeasons[0]) : null;
  const currentPoster = activeSeasonObj?.poster || item?.season_poster || item?.poster;
  const currentEpInfo = episodes_info.find((ep) => ep.episode_number === episode);
  const activeThumbnail = currentEpInfo?.still || current_thumbnail || currentPoster;
  const totalEpisodesInSeason = activeSeasonObj?.episodes || 8;

  const handleNextServer = () => {
    if (playerMode === "videojs") {
      setPlayerMode("servers");
      handleServerSelect(0);
    } else {
      const total = streaming_servers.length || 10;
      const nextIdx = (activeServer + 1) % total;
      handleServerSelect(nextIdx);
    }
  };

  return (
    <div className="container" style={{ paddingTop: "24px", paddingBottom: "80px" }}>
      {isWatchMode ? (
        /* =========================================================================
           DEDICATED CINEMA PLAYER SCREEN (NetMirror Exact Layout - Image 2)
           ========================================================================= */
        <div>
          {/* 1. Breadcrumbs & Back to Details Action */}
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "14px",
            color: "#64748b",
            marginBottom: "20px",
            flexWrap: "wrap",
            gap: "10px"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Link to="/" style={{ color: "#38bdf8", textDecoration: "none" }}>Home</Link>
              <span>&gt;</span>
              <span style={{ color: "#94a3b8" }}>{item.title}</span>
              {isTvSeries && (
                <>
                  <span>&gt;</span>
                  <span style={{ color: "#38bdf8", fontWeight: "600" }}>Season {season}</span>
                </>
              )}
            </div>

            <button
              onClick={handleBackToDetails}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                background: "rgba(255, 255, 255, 0.08)",
                border: "1px solid rgba(255, 255, 255, 0.18)",
                color: "#e2e8f0",
                fontSize: "13px",
                fontWeight: "700",
                padding: "6px 14px",
                borderRadius: "6px",
                cursor: "pointer",
                transition: "all 0.2s"
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.15)"}
              onMouseLeave={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.08)"}
            >
              <ArrowLeft size={16} /> Back to Details
            </button>
          </div>

          {/* 2. Server Switcher Bar (NetMirror Screenshot Exact Match: Server 1, Server 2, Server 3, etc.) */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            flexWrap: "wrap",
            marginBottom: "8px",
            background: "#081325",
            padding: "8px 12px",
            borderRadius: "8px",
            border: "1px solid rgba(255,255,255,0.08)"
          }}>
            {streaming_servers.map((srv, idx) => (
              <button
                key={srv.id}
                onClick={() => handleServerSelect(idx)}
                style={{
                  padding: "6px 16px",
                  fontSize: "13px",
                  fontWeight: "700",
                  borderRadius: "6px",
                  cursor: "pointer",
                  background: activeServer === idx ? "#eab308" : "#1e293b",
                  color: activeServer === idx ? "#0f172a" : "#cbd5e1",
                  border: activeServer === idx ? "1px solid #facc15" : "1px solid rgba(255,255,255,0.12)",
                  transition: "all 0.15s"
                }}
              >
                {srv.name}
              </button>
            ))}

            <button
              onClick={handleNextServer}
              style={{
                padding: "6px 14px",
                fontSize: "12px",
                fontWeight: "700",
                borderRadius: "6px",
                cursor: "pointer",
                background: "#0284c7",
                color: "#ffffff",
                border: "none",
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                marginLeft: "4px"
              }}
              title="Switch to next mirror server"
            >
              🔄 Next Server
            </button>

            {currentEmbedUrl && (
              <a
                href={currentEmbedUrl}
                target="_blank"
                rel="noreferrer noopener"
                style={{
                  marginLeft: "auto",
                  color: "#38bdf8",
                  fontSize: "12px",
                  fontWeight: "600",
                  textDecoration: "none",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px"
                }}
              >
                ↗ Open Tab
              </a>
            )}
          </div>


          {/* 3. Side-by-Side Video & Episode Layout (NetMirror Screenshot Exact Match) */}
          <div className="cinema-player-layout">
            {/* Left Main Video Area with Authentic Season & Episode Thumbnails */}
            <div className="cinema-video-box">
              {!isPlaying ? (
                <div
                  onClick={() => setIsPlaying(true)}
                  style={{
                    width: "100%",
                    height: "100%",
                    backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.45), rgba(0, 0, 0, 0.75)), url(${activeThumbnail})`,
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    cursor: "pointer",
                    userSelect: "none"
                  }}
                  title="Click to start video"
                >
                  {/* Cineverse Spinning Cosmic Logo on Hover (Requested by User) */}
                  <div className="cineverse-hover-hub" title="Watch on Cineverse">
                    <div className="cineverse-orbit-ring" />
                    <div className="cineverse-orbit-ring-glow" />
                    <img
                      src="/cineverse-card.png"
                      alt="Cineverse"
                      className="cineverse-center-logo"
                    />
                    <div className="cineverse-play-badge">
                      <Play size={16} fill="#ffffff" color="#ffffff" style={{ marginLeft: "2px" }} />
                    </div>
                  </div>

                  {/* Title overlay matching user screenshot */}
                  <div style={{
                    fontSize: "15px",
                    fontWeight: "700",
                    color: "#ffffff",
                    textShadow: "0 2px 10px rgba(0,0,0,0.9)",
                    background: "rgba(0, 0, 0, 0.72)",
                    padding: "6px 20px",
                    borderRadius: "20px",
                    border: "1px solid rgba(255, 255, 255, 0.18)",
                    backdropFilter: "blur(6px)"
                  }}>
                    {item.title} ({item.year || "2024"}) {isTvSeries ? `(S${season < 10 ? '0' + season : season}E${episode < 10 ? '0' + episode : episode})` : ""}
                  </div>

                  {/* Indicator with glowing Cineverse accent */}
                  <div style={{
                    fontSize: "12px",
                    color: "#38bdf8",
                    marginTop: "10px",
                    fontWeight: "700",
                    textShadow: "0 1px 6px rgba(0,0,0,0.9)",
                    letterSpacing: "0.3px",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px"
                  }}>
                    <span>✨</span> Click to Stream on Cineverse • Server {activeServer + 1}
                  </div>
                </div>
              ) : (streaming_servers[activeServer]?.is_direct && directStreamUrl) ? (
                /* Adaptive HLS & CDN Cinema Player */
                <VideoPlayer
                  key={`vjs-${streaming_servers[activeServer]?.url}-${season}-${episode}`}
                  src={streaming_servers[activeServer]?.url || directStreamUrl}
                  poster={activeThumbnail}
                  title={item.title}
                  initialTime={resume_seconds}
                  onProgress={(curr, dur) => updatePlaybackProgress(item.id, curr, dur)}
                  onSwitchServer={handleNextServer}
                />
              ) : (
                /* Cinema Multi-Server Embed Iframe (Servers 1-10) */
                <div style={{ position: "relative", width: "100%", height: "100%" }}>
                  {iframeLoading && (
                    <div className="iframe-fast-loader">
                      <div className="fast-loader-spinner" />
                      <div style={{ marginTop: "14px", fontWeight: "700", fontSize: "14px", color: "#f8fafc" }}>
                        Connecting to Server {activeServer + 1}...
                      </div>
                      <div style={{ fontSize: "12px", color: "#38bdf8", marginTop: "4px" }}>
                        ⚡ Optimizing high-speed 1080p stream
                      </div>
                    {showSlowWarning && (
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
                        <button
                          type="button"
                          onClick={handleNextServer}
                          className="auto-failover-pill"
                        >
                          ⚡ Server taking too long? Click to Switch to Server {((activeServer + 1) % (streaming_servers.length || 10)) + 1}
                        </button>
                        <span style={{ fontSize: "11px", color: "#94a3b8" }}>
                          Tip: Different servers host streams from different global CDN locations.
                        </span>
                      </div>
                    )}
                    </div>
                  )}
                  <iframe
                    key={`${currentEmbedUrl}-${activeServer}-${season}-${episode}`}
                    src={currentEmbedUrl}
                    title={item.title}
                    style={{ width: "100%", height: "100%", border: "none", display: "block" }}
                    referrerPolicy="origin"
                    loading="eager"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; fullscreen"
                    allowFullScreen
                    onLoad={() => { setIframeLoading(false); setShowSlowWarning(false); }}
                  />
                </div>
              )}
            </div>

            {/* Right Side Seasons & Episodes Panel (Shown for TV Series with authentic seasons) */}
            {isTvSeries && effectiveSeasons && effectiveSeasons.length > 0 && (
              <div className="cinema-episodes-panel">
                {/* Season Buttons */}
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  {effectiveSeasons.map((s) => (
                    <button
                      key={s.season}
                      onClick={() => { setSeason(s.season); setEpisode(1); setIsPlaying(true); }}
                      style={{
                        padding: "6px 14px",
                        fontSize: "13px",
                        fontWeight: "800",
                        borderRadius: "6px",
                        cursor: "pointer",
                        background: season === s.season ? "#eab308" : "#1e293b",
                        color: season === s.season ? "#0f172a" : "#cbd5e1",
                        border: season === s.season ? "1px solid #facc15" : "1px solid rgba(255,255,255,0.12)"
                      }}
                    >
                      SE{s.season}
                    </button>
                  ))}
                </div>

                {/* Episode Numbers Grid (5 buttons per row) */}
                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(5, 1fr)",
                  gap: "6px"
                }}>
                  {Array.from({ length: totalEpisodesInSeason }, (_, i) => i + 1).map((ep) => (
                    <button
                      key={ep}
                      onClick={() => { setEpisode(ep); setIsPlaying(true); }}
                      style={{
                        padding: "8px 0",
                        textAlign: "center",
                        fontSize: "13px",
                        fontWeight: "700",
                        borderRadius: "4px",
                        cursor: "pointer",
                        background: episode === ep ? "#22c55e" : "#334155",
                        color: "#ffffff",
                        border: episode === ep ? "1px solid #4ade80" : "1px solid rgba(255,255,255,0.08)"
                      }}
                    >
                      {ep}
                    </button>
                  ))}
                </div>

                {/* Authentic Episode Still / Thumbnail Preview */}
                <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: "8px" }}>
                  {activeThumbnail && (
                    <div style={{
                      position: "relative",
                      width: "100%",
                      height: "115px",
                      borderRadius: "6px",
                      overflow: "hidden",
                      border: "1px solid rgba(255,255,255,0.12)",
                      background: "#040d1a"
                    }}>
                      <img
                        key={activeThumbnail}
                        src={activeThumbnail}
                        alt={`S${season} E${episode}`}
                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        onError={(e) => { e.target.src = currentPoster; }}
                      />
                      <div style={{
                        position: "absolute",
                        bottom: 0,
                        left: 0,
                        right: 0,
                        padding: "4px 8px",
                        background: "linear-gradient(transparent, rgba(0,0,0,0.85))",
                        fontSize: "11px",
                        fontWeight: "700",
                        color: "#ffffff",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis"
                      }}>
                        {currentEpInfo?.name || `Episode ${episode}`}
                      </div>
                    </div>
                  )}

                  {/* Selected Indicator Box (Exact match with NetMirror) */}
                  <div style={{
                    padding: "8px 10px",
                    border: "1px solid #38bdf8",
                    borderRadius: "6px",
                    color: "#38bdf8",
                    fontSize: "12px",
                    fontWeight: "700",
                    textAlign: "center",
                    background: "rgba(56, 189, 248, 0.08)"
                  }}>
                    Season {season} Selected Episode: {episode}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* =========================================================================
           MOVIE DETAILS SCREEN (NetMirror Exact Layout - Image 1)
           ========================================================================= */
        <div>
          {/* 1. Breadcrumbs */}
          <div style={{ fontSize: "14px", color: "#64748b", marginBottom: "24px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Link to="/" style={{ color: "#38bdf8", textDecoration: "none" }}>Home</Link>
            <span>&gt;</span>
            <span style={{ color: "#94a3b8" }}>{item.title}</span>
            {isTvSeries && (
              <>
                <span>&gt;</span>
                <span style={{ color: "#38bdf8", fontWeight: "600" }}>Season {season}</span>
              </>
            )}
          </div>

          {/* 2. Hero Detail Header (NetMirror Exact Layout) */}
          <div style={{ display: "flex", gap: "32px", marginBottom: "36px", flexWrap: "wrap", alignItems: "flex-start" }}>
            {/* Left Poster (Dynamic: updates when season changes!) */}
            <div style={{ width: "200px", flexShrink: 0 }}>
              <img
                src={currentPoster}
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

                {/* Watch Free Button (Bright NetMirror Style - Triggers Dedicated Cinema Player) */}
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

          {/* 4. Clean Cinema Trailer Section (No YouTube Branding / Watermarks) */}
          <TrailerPlayer trailer={trailer} poster={item.poster} title={item.title} />

          {/* 5. Starring Section (Circular Avatars - Screenshot 2 Exact) */}
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
        </div>
      )}

      {/* Similar Title Carousel (Displayed on both views at the bottom, matching NetMirror) */}
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
