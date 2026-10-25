import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { LayoutGrid } from "lucide-react";
import MovieCard from "../components/MovieCard";
import { searchMovies } from "../services/api";

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const q = searchParams.get("q") || "";
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!q.trim()) {
      setResults([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    searchMovies(q.trim())
      .then((data) => {
        setResults(data.results || []);
      })
      .catch((err) => {
        console.error("Search error:", err);
        setResults([]);
      })
      .finally(() => setLoading(false));
  }, [q]);

  return (
    <div className="container" style={{ paddingTop: "28px", paddingBottom: "80px" }}>
      {/* Grid View Header matching user screenshot */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "24px" }}>
        <LayoutGrid size={22} color="#ffffff" />
        <h2 style={{ fontSize: "22px", fontWeight: "800", color: "#ffffff", letterSpacing: "-0.4px" }}>
          Grid View
        </h2>
        {q && (
          <span style={{ fontSize: "14px", color: "#94a3b8", marginLeft: "6px" }}>
            ({results.length} titles found for "{q}")
          </span>
        )}
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: "80px 0", color: "#94a3b8" }}>
          Searching movies and series...
        </div>
      ) : results.length > 0 ? (
        <div className="movie-grid">
          {results.map((item) => (
            <MovieCard key={item.id} item={item} />
          ))}
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: "80px 0", color: "#94a3b8" }}>
          <h3 style={{ fontSize: "20px", color: "#e2e8f0" }}>No titles found for "{q}"</h3>
          <p style={{ marginTop: "10px", fontSize: "14px" }}>
            Try searching with another keyword or explore categories on the Home page.
          </p>
        </div>
      )}
    </div>
  );
}
