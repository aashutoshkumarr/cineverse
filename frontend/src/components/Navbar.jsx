import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Search, Film, Bookmark, Clock, X } from "lucide-react";
import { searchMovies, fetchWatchlist, fetchHistory } from "../services/api";

export default function Navbar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [watchlistCount, setWatchlistCount] = useState(0);
  const [historyCount, setHistoryCount] = useState(0);
  const searchRef = useRef(null);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  // Load counts & close dropdown on route change
  useEffect(() => {
    fetchWatchlist().then(data => setWatchlistCount(data.length)).catch(() => {});
    fetchHistory().then(data => setHistoryCount(data.length)).catch(() => {});
    setShowDropdown(false);
  }, [location.pathname, location.search]);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const data = await searchMovies(query);
        setResults(data.results || []);
        // Only show dropdown if input is currently focused AND not on /search page
        if (document.activeElement === inputRef.current && location.pathname !== "/search") {
          setShowDropdown(true);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsSearching(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [query, location.pathname]);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (item) => {
    setShowDropdown(false);
    setQuery("");
    inputRef.current?.blur();
    navigate(`/watch/${item.id}?type=${item.media_type || 'movie'}`);
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setShowDropdown(false);
    inputRef.current?.blur();
    navigate(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <header className="navbar">
      <div className="container nav-content">
        {/* Brand Logo */}
        <Link to="/" className="logo-text" style={{ display: "flex", alignItems: "center", gap: "10px", textDecoration: "none" }}>
          <img
            src="/cineverse-card.png"
            alt="Cineverse"
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              boxShadow: "0 0 18px rgba(217, 70, 239, 0.45)",
              border: "1px solid rgba(255, 255, 255, 0.18)",
              objectFit: "cover"
            }}
          />
          <div style={{ display: "flex", flexDirection: "column", lineHeight: 1 }}>
            <span style={{ fontSize: "22px", fontWeight: "900", letterSpacing: "-0.5px" }}>
              Cine<span style={{ background: "linear-gradient(135deg, #ec4899 0%, #a855f7 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>verse</span>
            </span>
            <span style={{ fontSize: "9px", fontWeight: "700", color: "#94a3b8", letterSpacing: "0.6px", marginTop: "4px" }}>
              YOUR UNIVERSE OF ENTERTAINMENT
            </span>
          </div>
        </Link>

        {/* Global Instant Search */}
        <div className="search-box" ref={searchRef}>
          <form className="search-form" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              className="search-input"
              placeholder="Search for movie or TV show.."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => query.trim() && location.pathname !== "/search" && setShowDropdown(true)}
              onKeyDown={(e) => {
                if (e.key === "Escape") setShowDropdown(false);
              }}
            />
            {query && (
              <button
                type="button"
                onClick={() => { setQuery(""); setShowDropdown(false); }}
                className="search-clear-btn"
                aria-label="Clear search"
              >
                <X size={16} />
              </button>
            )}
            <button type="submit" className="search-submit-btn">
              Search
            </button>
          </form>

          {/* Search Dropdown Popup */}
          {showDropdown && results.length > 0 && (
            <div className="search-dropdown">
              {results.slice(0, 8).map((item) => (
                <div
                  key={item.id}
                  className="search-item"
                  onClick={() => handleSelect(item)}
                >
                  <img
                    src={item.poster || "https://image.tmdb.org/t/p/w200"}
                    alt={item.title}
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: "14px", fontWeight: "600", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {item.title}
                    </div>
                    <div style={{ fontSize: "12px", color: "#94a3b8" }}>
                      ⭐ {item.rating} • {item.year} • {item.category || item.media_type?.toUpperCase()}
                    </div>
                  </div>
                </div>
              ))}
              <div
                className="search-item"
                style={{ borderTop: "1px solid rgba(255, 255, 255, 0.1)", justifyContent: "center", color: "#38bdf8", fontWeight: "700", fontSize: "13px", marginTop: "4px", padding: "10px" }}
                onClick={handleSubmit}
              >
                <span>⊞ View all "{query}" results in Grid View →</span>
              </div>
            </div>
          )}
        </div>

        {/* Navbar Action Links */}
        <nav className="nav-links">
          <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
            Home
          </Link>
          <Link to="/watchlist" className={`nav-link ${location.pathname === '/watchlist' ? 'active' : ''}`}>
            <Bookmark size={16} />
            <span>Watchlist</span>
            {watchlistCount > 0 && <span className="badge-counter">{watchlistCount}</span>}
          </Link>
          <Link to="/history" className={`nav-link ${location.pathname === '/history' ? 'active' : ''}`}>
            <Clock size={16} />
            <span>History</span>
            {historyCount > 0 && <span className="badge-counter">{historyCount}</span>}
          </Link>
        </nav>
      </div>
    </header>
  );
}
