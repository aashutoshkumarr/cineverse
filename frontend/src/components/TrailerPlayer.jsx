import React, { useRef } from "react";

export default function TrailerPlayer({ trailer, poster, title }) {
  const videoRef = useRef(null);

  if (!trailer) {
    return null;
  }

  const isMp4 = trailer.is_mp4 || (trailer.mp4_url && trailer.mp4_url.includes(".mp4"));
  const mp4Src = trailer.mp4_url;

  return (
    <div style={{ marginBottom: "44px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "24px" }}>
      <h2 style={{ fontSize: "18px", fontWeight: "800", color: "#ffffff", marginBottom: "16px" }}>
        Trailer:
      </h2>

      <div
        style={{
          maxWidth: "680px",
          width: "100%",
          aspectRatio: "16 / 9",
          borderRadius: "10px",
          overflow: "hidden",
          background: "#000000",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.75)",
          position: "relative"
        }}
      >
        {isMp4 && mp4Src ? (
          /* Exact NetMirror Native HTML5 Video Player (Zero YouTube branding) */
          <video
            ref={videoRef}
            src={mp4Src}
            controls
            autoPlay
            muted
            loop
            playsInline
            poster={poster}
            style={{
              width: "100%",
              height: "100%",
              display: "block",
              objectFit: "contain",
              backgroundColor: "#000000"
            }}
          >
            <source src={mp4Src} type="video/mp4" />
            Your browser does not support HTML5 video.
          </video>
        ) : trailer.youtube_key || trailer.embed_url ? (
          /* Clean cropped player masking out YouTube Title banner and watermark */
          <div
            style={{
              position: "relative",
              width: "100%",
              height: "100%",
              overflow: "hidden",
              background: "#000000"
            }}
          >
            <iframe
              src={`https://www.youtube-nocookie.com/embed/${trailer.youtube_key || ''}?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&showinfo=0&disablekb=1`}
              title={`${title} Trailer`}
              style={{
                position: "absolute",
                top: "-55px",
                left: 0,
                width: "100%",
                height: "calc(100% + 55px)",
                border: "none"
              }}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#94a3b8", fontSize: "14px" }}>
            Trailer not available
          </div>
        )}
      </div>
    </div>
  );
}
