import React, { useRef, useEffect } from "react";

export default function VideoPlayer({
  src,
  poster,
  type = "hls",
  initialTime = 0,
  onProgress = null,
  title = "Movie Player"
}) {
  const videoRef = useRef(null);
  const lastSaved = useRef(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (initialTime > 5) {
      video.currentTime = initialTime;
    }

    const handleTimeUpdate = () => {
      const current = video.currentTime;
      const duration = video.duration || 0;
      if (onProgress && Math.abs(current - lastSaved.current) > 5) {
        lastSaved.current = current;
        onProgress(current, duration);
      }
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [src, initialTime, onProgress]);

  return (
    <div
      style={{
        width: "100%",
        aspectRatio: "16 / 9",
        borderRadius: "14px",
        overflow: "hidden",
        boxShadow: "0 20px 50px rgba(0,0,0,0.8)",
        background: "#000000",
        border: "1px solid rgba(255,255,255,0.12)",
        position: "relative"
      }}
    >
      <video
        ref={videoRef}
        src={src}
        controls
        autoPlay
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
        <source src={src} type={src && src.includes(".m3u8") ? "application/x-mpegURL" : "video/mp4"} />
        Your browser does not support video playback.
      </video>
    </div>
  );
}
