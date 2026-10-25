import React, { useRef, useEffect, useState } from "react";
import Hls from "hls.js";
import { Play, Pause, Volume2, VolumeX, Maximize, RotateCcw, FastForward, Loader2 } from "lucide-react";

/**
 * Adaptive Cinema Video Player (HLS & Direct CDN) for Cineverse.
 * Powered by Hls.js + HTML5 Native Video Engine.
 * Features: Adaptive bitrate, HD quality, smooth buffering, custom Cineverse theme,
 * auto-resume, playback rate controls, full error handling.
 */
export default function VideoPlayer({
  src,
  poster,
  initialTime = 0,
  onProgress = null,
  title = "Now Playing",
  onSwitchServer = null
}) {
  const videoRef = useRef(null);
  const containerRef = useRef(null);
  const hlsRef = useRef(null);
  const lastSavedTime = useRef(0);

  const [isPlaying, setIsPlaying] = useState(false);
  const [isBuffering, setIsBuffering] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showControls, setShowControls] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const controlsTimeoutRef = useRef(null);

  // Keep latest onProgress in ref to avoid re-initializing video on parent re-renders
  const onProgressRef = useRef(onProgress);
  useEffect(() => {
    onProgressRef.current = onProgress;
  }, [onProgress]);

  // Clean up controls timer on unmount
  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !src) return;

    setHasError(false);
    setErrorMessage("");
    setIsBuffering(true);

    // Clean up previous HLS instance if any
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    const isHlsUrl = src.includes(".m3u8") || src.includes("/manifest");

    if (isHlsUrl && Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90
      });
      hlsRef.current = hls;

      hls.loadSource(src);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setIsBuffering(false);
        if (initialTime > 5) {
          video.currentTime = initialTime;
        }
        video.play().then(() => setIsPlaying(true)).catch(() => {
          video.muted = true;
          setIsMuted(true);
          video.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
        });
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              hls.recoverMediaError();
              break;
            default:
              setHasError(true);
              setErrorMessage("Streaming manifest error. Please switch servers.");
              hls.destroy();
              break;
          }
        }
      });
    } else if (isHlsUrl && video.canPlayType("application/vnd.apple.mpegurl")) {
      // Native Apple Safari HLS
      video.src = src;
      if (initialTime > 5) video.currentTime = initialTime;
      video.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    } else {
      // Native MP4 / WebM / CDN Video
      video.src = src;
      video.load();
      if (initialTime > 5) video.currentTime = initialTime;
      video.play().then(() => setIsPlaying(true)).catch(() => {
        video.muted = true;
        setIsMuted(true);
        video.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
      });
    }

    const handleLoadedMetadata = () => {
      setDuration(video.duration || 0);
      setIsBuffering(false);
      if (initialTime > 5) {
        video.currentTime = initialTime;
      }
    };

    const handleTimeUpdate = () => {
      const curr = video.currentTime;
      const dur = video.duration || 0;
      setCurrentTime(curr);
      setDuration(dur);

      if (onProgressRef.current && Math.abs(curr - lastSavedTime.current) > 5) {
        lastSavedTime.current = curr;
        onProgressRef.current(curr, dur);
      }
    };

    const handlePlay = () => {
      setIsPlaying(true);
      setIsBuffering(false);
    };

    const handlePause = () => {
      setIsPlaying(false);
    };

    const handleWaiting = () => {
      setIsBuffering(true);
    };

    const handlePlaying = () => {
      setIsBuffering(false);
      setIsPlaying(true);
    };

    const handleError = () => {
      setHasError(true);
      setIsBuffering(false);
      setIsPlaying(false);
      setErrorMessage("Video playback failed on this stream.");
    };

    video.addEventListener("loadedmetadata", handleLoadedMetadata);
    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("play", handlePlay);
    video.addEventListener("pause", handlePause);
    video.addEventListener("waiting", handleWaiting);
    video.addEventListener("playing", handlePlaying);
    video.addEventListener("error", handleError);

    return () => {
      video.removeEventListener("loadedmetadata", handleLoadedMetadata);
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("pause", handlePause);
      video.removeEventListener("waiting", handleWaiting);
      video.removeEventListener("playing", handlePlaying);
      video.removeEventListener("error", handleError);

      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, [src, initialTime]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch((err) => {
        console.warn("Autoplay block, unmuting requirement:", err);
        // Fallback with user interaction
        videoRef.current.muted = false;
        videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
      });
    }
  };

  const handleSeek = (e) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    const nextMuted = !isMuted;
    videoRef.current.muted = nextMuted;
    setIsMuted(nextMuted);
  };

  const handleVolumeChange = (e) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (videoRef.current) {
      videoRef.current.volume = val;
      videoRef.current.muted = val === 0;
      setIsMuted(val === 0);
    }
  };

  const handleRateChange = (rate) => {
    setPlaybackRate(rate);
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  const formatTime = (secs) => {
    if (!secs || isNaN(secs)) return "00:00";
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m < 10 ? "0" + m : m}:${s < 10 ? "0" + s : s}`;
  };

  const handleMouseMove = () => {
    setShowControls(true);
    if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
    controlsTimeoutRef.current = setTimeout(() => {
      if (isPlaying) setShowControls(false);
    }, 2800);
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => isPlaying && setShowControls(false)}
      style={{
        width: "100%",
        height: "100%",
        background: "#000000",
        borderRadius: "10px",
        overflow: "hidden",
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        userSelect: "none"
      }}
    >
      <video
        ref={videoRef}
        poster={poster}
        playsInline
        preload="auto"
        style={{
          width: "100%",
          height: "100%",
          objectFit: "contain",
          backgroundColor: "#000000",
          cursor: "pointer"
        }}
        onClick={togglePlay}
      />

      {/* Top Overlay Header */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          padding: "14px 20px",
          background: "linear-gradient(180deg, rgba(0,0,0,0.85) 0%, transparent 100%)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          opacity: showControls ? 1 : 0,
          transition: "opacity 0.3s ease",
          pointerEvents: showControls ? "auto" : "none"
        }}
      >
        <span style={{ fontSize: "14px", fontWeight: "700", color: "#ffffff", textShadow: "0 2px 8px rgba(0,0,0,0.8)" }}>
          {title}
        </span>
        <span style={{ fontSize: "11px", fontWeight: "700", color: "#38bdf8", background: "rgba(56, 189, 248, 0.15)", padding: "3px 10px", borderRadius: "12px", border: "1px solid rgba(56, 189, 248, 0.3)" }}>
          Ultra HD 1080p • HLS Cinema
        </span>
      </div>

      {/* Buffering Spinner */}
      {isBuffering && !hasError && (
        <div
          style={{
            position: "absolute",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "10px",
            color: "#38bdf8",
            pointerEvents: "none"
          }}
        >
          <Loader2 className="animate-spin" size={44} />
          <span style={{ fontSize: "12px", fontWeight: "700", color: "#cbd5e1", textShadow: "0 2px 8px rgba(0,0,0,0.8)" }}>
            Buffering Stream...
          </span>
        </div>
      )}

      {/* Error state fallback overlay */}
      {hasError ? (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "rgba(0, 0, 0, 0.9)",
            backdropFilter: "blur(6px)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
            textAlign: "center",
            zIndex: 10
          }}
        >
          <div style={{ fontSize: "32px", marginBottom: "8px" }}>🎬</div>
          <div style={{ color: "#ffffff", fontSize: "16px", fontWeight: "700", marginBottom: "6px" }}>
            {errorMessage || "Direct Stream Unavailable"}
          </div>
          <div style={{ color: "#94a3b8", fontSize: "13px", maxWidth: "420px", marginBottom: "16px" }}>
            Please select another server from <b>Server 1 to Server 10</b> above for guaranteed playback.
          </div>
          {onSwitchServer && (
            <button
              onClick={onSwitchServer}
              style={{
                background: "#eab308",
                color: "#0f172a",
                fontWeight: "700",
                fontSize: "13px",
                padding: "8px 18px",
                borderRadius: "6px",
                border: "none",
                cursor: "pointer"
              }}
            >
              Switch to Next Server
            </button>
          )}
        </div>
      ) : !isPlaying && !isBuffering && (
        <div
          onClick={togglePlay}
          style={{
            position: "absolute",
            width: "72px",
            height: "72px",
            borderRadius: "50%",
            background: "rgba(14, 165, 233, 0.9)",
            border: "2px solid #38bdf8",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            boxShadow: "0 0 35px rgba(56, 189, 248, 0.8)",
            transition: "transform 0.2s"
          }}
          onMouseEnter={(e) => e.currentTarget.style.transform = "scale(1.1)"}
          onMouseLeave={(e) => e.currentTarget.style.transform = "scale(1)"}
        >
          <Play size={32} fill="#ffffff" color="#ffffff" style={{ marginLeft: "4px" }} />
        </div>
      )}

      {/* Bottom Cineverse Control Bar */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          padding: "16px 20px 12px",
          background: "linear-gradient(0deg, rgba(4, 12, 26, 0.96) 0%, rgba(4, 12, 26, 0.7) 70%, transparent 100%)",
          opacity: showControls ? 1 : 0,
          transition: "opacity 0.3s ease",
          pointerEvents: showControls ? "auto" : "none",
          display: "flex",
          flexDirection: "column",
          gap: "8px"
        }}
      >
        {/* Progress Scrubber */}
        <input
          type="range"
          min="0"
          max={duration || 100}
          value={currentTime}
          onChange={handleSeek}
          style={{
            width: "100%",
            height: "5px",
            borderRadius: "3px",
            accentColor: "#38bdf8",
            cursor: "pointer",
            background: "rgba(255,255,255,0.2)"
          }}
        />

        {/* Buttons Row */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          {/* Left Controls: Play/Pause, Volume, Time */}
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <button
              onClick={togglePlay}
              style={{ background: "none", border: "none", color: "#ffffff", cursor: "pointer", display: "flex", alignItems: "center" }}
            >
              {isPlaying ? <Pause size={20} /> : <Play size={20} fill="#ffffff" />}
            </button>

            {/* Volume */}
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <button
                onClick={toggleMute}
                style={{ background: "none", border: "none", color: "#ffffff", cursor: "pointer", display: "flex", alignItems: "center" }}
              >
                {isMuted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                style={{ width: "65px", height: "4px", accentColor: "#38bdf8", cursor: "pointer" }}
              />
            </div>

            {/* Time Display */}
            <span style={{ fontSize: "12px", color: "#cbd5e1", fontWeight: "600" }}>
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>

          {/* Right Controls: Speed Selector & Fullscreen */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* Speed Pills */}
            <div style={{ display: "flex", gap: "4px" }}>
              {[1, 1.25, 1.5].map((rate) => (
                <button
                  key={rate}
                  onClick={() => handleRateChange(rate)}
                  style={{
                    background: playbackRate === rate ? "#38bdf8" : "rgba(255,255,255,0.1)",
                    color: playbackRate === rate ? "#041226" : "#cbd5e1",
                    border: "none",
                    borderRadius: "4px",
                    padding: "2px 8px",
                    fontSize: "11px",
                    fontWeight: "700",
                    cursor: "pointer"
                  }}
                >
                  {rate}x
                </button>
              ))}
            </div>

            <button
              onClick={toggleFullscreen}
              style={{ background: "none", border: "none", color: "#ffffff", cursor: "pointer", display: "flex", alignItems: "center" }}
              title="Fullscreen"
            >
              <Maximize size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
