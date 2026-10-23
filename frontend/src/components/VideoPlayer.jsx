import React, { useEffect, useRef } from "react";
import videojs from "video.js";
import "video.js/dist/video-js.css";

export default function VideoPlayer({
  src,
  poster,
  type = "hls",
  initialTime = 0,
  onProgress = null,
  title = "Movie Player"
}) {
  const videoRef = useRef(null);
  const playerRef = useRef(null);
  const lastSavedTime = useRef(0);

  useEffect(() => {
    // Determine MIME type
    const mimeType =
      type === "hls" || (src && src.includes(".m3u8"))
        ? "application/x-mpegURL"
        : "video/mp4";

    if (!playerRef.current) {
      const videoElement = document.createElement("video-js");
      videoElement.classList.add("vjs-big-play-centered", "vjs-netflix-skin");
      videoRef.current.appendChild(videoElement);

      const player = (playerRef.current = videojs(
        videoElement,
        {
          autoplay: false,
          controls: true,
          responsive: true,
          fluid: true,
          poster: poster,
          preload: "auto",
          playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 2],
          sources: [
            {
              src: src,
              type: mimeType
            }
          ],
          controlBar: {
            pictureInPictureToggle: true,
            volumePanel: { inline: false }
          }
        },
        () => {
          // If resuming from previous watch time
          if (initialTime > 5) {
            player.currentTime(initialTime);
          }
        }
      ));

      // Track playback progress
      player.on("timeupdate", () => {
        const current = player.currentTime();
        const duration = player.duration();

        // Throttle saving progress to every 5 seconds
        if (onProgress && Math.abs(current - lastSavedTime.current) > 5) {
          lastSavedTime.current = current;
          onProgress(current, duration);
        }
      });

      player.on("ended", () => {
        if (onProgress) {
          const duration = player.duration();
          onProgress(duration, duration);
        }
      });
    } else {
      const player = playerRef.current;
      player.src({
        src: src,
        type: mimeType
      });
      if (poster) {
        player.poster(poster);
      }
      if (initialTime > 5) {
        player.currentTime(initialTime);
      }
    }

    return () => {
      if (playerRef.current && !playerRef.current.isDisposed()) {
        playerRef.current.dispose();
        playerRef.current = null;
      }
    };
  }, [src, type]);

  return (
    <div
      style={{
        width: "100%",
        borderRadius: "14px",
        overflow: "hidden",
        boxShadow: "0 20px 50px rgba(0,0,0,0.8)",
        background: "#000000",
        border: "1px solid rgba(255,255,255,0.12)",
        position: "relative"
      }}
    >
      <div ref={videoRef} />
    </div>
  );
}
