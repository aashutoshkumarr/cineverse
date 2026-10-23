import React, { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import MovieCard from "./MovieCard";

export default function MovieShelf({ shelf }) {
  const rowRef = useRef(null);

  if (!shelf || !shelf.items || shelf.items.length === 0) return null;

  const scroll = (direction) => {
    if (rowRef.current) {
      const scrollAmount = 600;
      rowRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth"
      });
    }
  };

  return (
    <div className="shelf-container">
      <div className="shelf-header">
        <h2 className="shelf-title">
          <span>{shelf.title}</span>
          {shelf.tag && <span className="shelf-tag">{shelf.tag}</span>}
        </h2>
      </div>

      <button className="scroll-arrow left" onClick={() => scroll("left")} aria-label="Scroll left">
        <ChevronLeft size={22} />
      </button>

      <div className="shelf-scroll-row" ref={rowRef}>
        {shelf.items.map((item) => (
          <MovieCard key={item.id} item={item} />
        ))}
      </div>

      <button className="scroll-arrow right" onClick={() => scroll("right")} aria-label="Scroll right">
        <ChevronRight size={22} />
      </button>
    </div>
  );
}
