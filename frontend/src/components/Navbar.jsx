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
  const navigate = useNavigate();
  const location = useLocation();

  // Load counts
  useEffect(() => {
    fetchWatchlist().then(data => setWatchlistCount(data.length)).catch(() => {});
    fetchHistory().then(data => setHistoryCount(data.length)).catch(() => {});
  }, [location.pathname]);

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
        setShowDropdown(true);
      } catch (err) {
        console.error(err);
      } finally {
        setIsSearching(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [query]);

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
    navigate(`/watch/${item.id}?type=${item.media_type || 'movie'}`);
  };

  return (
    <header className="navbar">
      <div className="container nav-content">
        {/* Brand Logo */}
        <Link to="/" className="logo-text">
          <Film size={26} color="#00e676" />
          <span>Movie<span className="logo-highlight">Recommender</span></span>
        </Link>

        {/* Global Instant Search */}
        <div className="search-box" ref={searchRef}>
          <Search size={18} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search 2,490+ movies, cartoons, anime or K-dramas..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => query.trim() && setShowDropdown(true)}
          />
          {query && (
            <button
              onClick={() => { setQuery(""); setShowDropdown(false); }}
              style={{ position: "absolute", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", color: "#94a3b8", cursor: "pointer" }}
            >
              <X size={16} />
            </button>
          )}

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
