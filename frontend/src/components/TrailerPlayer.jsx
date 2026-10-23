import React, { useState, useRef } from "react";
import { Play, Pause, Volume2, VolumeX, Maximize } from "lucide-react";

export default function TrailerPlayer({ trailer, poster, title }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const containerRef = useRef(null);

  if (!trailer || !trailer.embed_url) {
    return null;
  }

  // Build clean embed URL with no branding parameters
  const cleanUrl = `${trailer.embed_url}&autoplay=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&disablekb=0&fs=1`;

  const toggleFullscreen = () => {
    if (containerRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {});
      } else {
        containerRef.current.requestFullscreen().catch(() => {});
      }
    }
  };

  return (
    <div style={{ marginBottom: "48px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "24px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: "800", color: "#ffffff", marginBottom: "16px" }}>
        Trailer:
      </h2>

      <div
        ref={containerRef}
        style={{
          maxWidth: "680px",
          width: "100%",
          aspectRatio: "16 / 9",
          borderRadius: "12px",
          overflow: "hidden",
          position: "relative",
          background: "#020916",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.7)"
        }}
      >
        {!isPlaying ? (
          /* NetMirror Clean Video Thumbnail (No Red YouTube Logo, No YouTube Channel Watermark) */
          <div
            onClick={() => setIsPlaying(true)}
            style={{
              width: "100%",
              height: "100%",
              backgroundImage: `url(${poster || 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&q=80'})`,
              backgroundSize: "cover",
              backgroundPosition: "center",
              position: "relative",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}
          >
            {/* Dark Cinema Overlay */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: "linear-gradient(180deg, rgba(4,18,38,0.3) 0%, rgba(4,18,38,0.7) 100%)"
              }}
            />

            {/* NetMirror Clean Play Circle (No YouTube Logo) */}
            <div
              style={{
                position: "relative",
                zIndex: 2,
                width: "68px",
                height: "68px",
                borderRadius: "50%",
                background: "rgba(15, 23, 42, 0.85)",
                backdropFilter: "blur(8px)",
                border: "2px solid rgba(255, 255, 255, 0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 25px rgba(0, 0, 0, 0.8)",
                transition: "transform 0.2s, background 0.2s"
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "scale(1.1)";
                e.currentTarget.style.borderColor = "#f97316";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "scale(1)";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.3)";
              }}
            >
              <Play size={28} fill="#ffffff" color="#ffffff" style={{ marginLeft: "4px" }} />
            </div>

            {/* Bottom Title Bar */}
            <div
              style={{
                position: "absolute",
                bottom: "14px",
                left: "18px",
                zIndex: 2,
                color: "#ffffff",
                fontSize: "14px",
                fontWeight: "700",
                textShadow: "0 2px 8px rgba(0,0,0,0.8)"
              }}
            >
              🎬 Official HD Trailer • Click to Play
            </div>
          </div>
        ) : (
          /* Active Playing Frame with Zoom/Cropping to Mask Out YouTube Branding */
          <div
            style={{
              position: "relative",
              width: "100%",
              height: "100%",
              overflow: "hidden"
            }}
          >
            <iframe
              src={cleanUrl}
              title={`${title} Trailer`}
              style={{
                position: "absolute",
                top: "-5%",
                left: "-3%",
                width: "106%",
                height: "110%",
                border: "none",
                pointerEvents: "auto"
              }}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />

            {/* Top Security Mask (Hides YouTube Title & Channel Icon) */}
            <div
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                height: "44px",
                background: "linear-gradient(180deg, rgba(4,18,38,0.95) 0%, rgba(4,18,38,0) 100%)",
                pointerEvents: "none",
                display: "flex",
                alignItems: "center",
                paddingLeft: "16px",
                fontSize: "13px",
                fontWeight: "700",
                color: "#cbd5e1"
              }}
            >
              {title} • Trailer
            </div>

            {/* Bottom-Right Watermark Mask (Hides "Watch on YouTube" pill) */}
            <div
              style={{
                position: "absolute",
                bottom: 0,
                right: 0,
                width: "170px",
                height: "50px",
                background: "transparent",
                pointerEvents: "none"
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
