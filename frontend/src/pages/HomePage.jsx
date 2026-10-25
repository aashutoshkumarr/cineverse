import React, { useState, useEffect, useRef, useCallback } from "react";
import HeroBanner from "../components/HeroBanner";
import FilterBar from "../components/FilterBar";
import MovieShelf from "../components/MovieShelf";
import MovieCard from "../components/MovieCard";
import { fetchShelves, fetchMovies } from "../services/api";
import { Compass, ArrowUp } from "lucide-react";

export default function HomePage() {
  const [shelves, setShelves] = useState([]);
  const [featured, setFeatured] = useState(null);

  // Filters
  const [country, setCountry] = useState("All");
  const [category, setCategory] = useState("All");
  const [language, setLanguage] = useState("All");

  // Filtered Infinite Stream
  const [filterMovies, setFilterMovies] = useState([]);
  const [filterPage, setFilterPage] = useState(1);
  const [filterTotalPages, setFilterTotalPages] = useState(1);
  const [filterTotalItems, setFilterTotalItems] = useState(0);
  const [loadingFilter, setLoadingFilter] = useState(false);

  // Continuous Discovery Feed Infinite Stream (Unfiltered)
  const [feedMovies, setFeedMovies] = useState([]);
  const [feedPage, setFeedPage] = useState(1);
  const [feedTotalPages, setFeedTotalPages] = useState(1);
  const [feedTotalItems, setFeedTotalItems] = useState(0);
  const [loadingFeed, setLoadingFeed] = useState(false);

  // Floating Back to Top
  const [showScrollTop, setShowScrollTop] = useState(false);

  const isFiltered = country !== "All" || category !== "All" || language !== "All";

  const feedSentinelRef = useRef(null);
  const filterSentinelRef = useRef(null);

  // Window scroll listener for floating back-to-top button
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 500);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // 1. Initial Load: Shelves, Featured Banner, and Initial Continuous Feed (Page 1)
  useEffect(() => {
    fetchShelves().then((data) => {
      setShelves(data);
      if (data.length > 0 && data[0].items.length > 0) {
        setFeatured(data[0].items[0]);
      }
    });

    setLoadingFeed(true);
    fetchMovies(1, 48, "All", "All", "All")
      .then((data) => {
        setFeedMovies(data.results || []);
        setFeedPage(1);
        setFeedTotalPages(data.total_pages || 1);
        setFeedTotalItems(data.total_items || 0);
      })
      .finally(() => setLoadingFeed(false));
  }, []);

  // 2. When Filters Change: Reset to Page 1 and Fetch
  useEffect(() => {
    if (!isFiltered) return;
    setLoadingFilter(true);
    setFilterMovies([]);
    setFilterPage(1);
    fetchMovies(1, 48, country, category, language)
      .then((data) => {
        setFilterMovies(data.results || []);
        setFilterPage(1);
        setFilterTotalPages(data.total_pages || 1);
        setFilterTotalItems(data.total_items || 0);
      })
      .finally(() => setLoadingFilter(false));
  }, [country, category, language, isFiltered]);

  // 3. Infinite Scroll for Continuous Discovery Feed
  const loadMoreFeed = useCallback(() => {
    if (loadingFeed || feedPage >= feedTotalPages) return;
    setLoadingFeed(true);
    const nextPage = feedPage + 1;
    fetchMovies(nextPage, 48, "All", "All", "All")
      .then((data) => {
        setFeedMovies((prev) => [...prev, ...(data.results || [])]);
        setFeedPage(nextPage);
        setFeedTotalPages(data.total_pages || 1);
      })
      .finally(() => setLoadingFeed(false));
  }, [loadingFeed, feedPage, feedTotalPages]);

  useEffect(() => {
    if (isFiltered) return;
    const sentinel = feedSentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loadingFeed && feedPage < feedTotalPages) {
          loadMoreFeed();
        }
      },
      { rootMargin: "400px" } // Pre-load 400px before user hits the bottom
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [isFiltered, loadingFeed, feedPage, feedTotalPages, loadMoreFeed]);

  // 4. Infinite Scroll for Filtered Grid
  const loadMoreFilter = useCallback(() => {
    if (loadingFilter || filterPage >= filterTotalPages) return;
    setLoadingFilter(true);
    const nextPage = filterPage + 1;
    fetchMovies(nextPage, 48, country, category, language)
      .then((data) => {
        setFilterMovies((prev) => [...prev, ...(data.results || [])]);
        setFilterPage(nextPage);
        setFilterTotalPages(data.total_pages || 1);
      })
      .finally(() => setLoadingFilter(false));
  }, [loadingFilter, filterPage, filterTotalPages, country, category, language]);

  useEffect(() => {
    if (!isFiltered) return;
    const sentinel = filterSentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loadingFilter && filterPage < filterTotalPages) {
          loadMoreFilter();
        }
      },
      { rootMargin: "400px" }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [isFiltered, loadingFilter, filterPage, filterTotalPages, loadMoreFilter]);

  const handleCountryChange = (c) => setCountry(c);
  const handleCategoryChange = (cat) => setCategory(cat);
  const handleLanguageChange = (l) => setLanguage(l);

  return (
    <div className="container" style={{ paddingBottom: "60px" }}>
      {/* Hero Banner (Only shown when not filtered) */}
      {!isFiltered && featured && <HeroBanner movie={featured} />}

      {/* Dynamic Filter Bar */}
      <FilterBar
        selectedCountry={country}
        onSelectCountry={handleCountryChange}
        selectedCategory={category}
        onSelectCategory={handleCategoryChange}
        selectedLanguage={language}
        onSelectLanguage={handleLanguageChange}
      />

      {/* If Filter is Active: Infinite Scroll Filtered Grid */}
      {isFiltered ? (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <h2 style={{ fontSize: "22px", fontWeight: "800" }}>
              📍 Filter Results: <span style={{ color: "#38bdf8" }}>{country} • {category} • {language}</span>
            </h2>
            <span style={{ color: "#94a3b8", fontSize: "14px" }}>
              Showing {filterMovies.length} of {filterTotalItems} titles
            </span>
          </div>

          {filterMovies.length > 0 ? (
            <>
              <div className="movie-grid">
                {filterMovies.map((item) => (
                  <MovieCard key={item.id} item={item} />
                ))}
              </div>

              {/* Infinite Scroll Sentinel for Filters */}
              {filterPage < filterTotalPages && (
                <div ref={filterSentinelRef} style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 0" }}>
                  <div className="infinite-scroll-spinner" />
                  <span style={{ fontSize: "13px", color: "#94a3b8", marginTop: "10px", fontWeight: "600" }}>
                    Loading more filtered titles...
                  </span>
                </div>
              )}

              {filterPage >= filterTotalPages && filterMovies.length > 0 && (
                <div style={{ textAlign: "center", padding: "40px 0", color: "#64748b", fontSize: "13px", fontWeight: "600" }}>
                  ✨ All {filterTotalItems} titles loaded
                </div>
              )}
            </>
          ) : loadingFilter ? (
            <div style={{ textAlign: "center", padding: "80px 0", color: "#94a3b8" }}>
              <div className="infinite-scroll-spinner" style={{ margin: "0 auto 12px" }} />
              Loading movies...
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "60px 20px", background: "rgba(255,255,255,0.02)", borderRadius: "16px" }}>
              <h3>No titles found for this filter</h3>
              <p style={{ color: "#94a3b8", marginTop: "8px" }}>Try selecting "All" or a different combination.</p>
            </div>
          )}
        </div>
      ) : (
        /* If No Filter is Active: Show Curated Shelves + Continuous Discovery Feed (Infinite Scroll) */
        <div>
          {shelves.map((shelf) => (
            <MovieShelf key={shelf.id} shelf={shelf} />
          ))}

          {/* Continuous Discovery Feed Header */}
          <div style={{ marginTop: "60px", marginBottom: "25px", borderBottom: "2px solid rgba(255,255,255,0.06)", paddingBottom: "14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "22px", fontWeight: "800", display: "flex", alignItems: "center", gap: "10px" }}>
              <Compass color="#f97316" />
              <span>Continuous Discovery Feed</span>
              <span className="badge-counter" style={{ fontSize: "13px" }}>2,500+ Titles Available</span>
            </h2>
            <span style={{ color: "#94a3b8", fontSize: "14px" }}>
              Scroll down to explore all movies & series automatically
            </span>
          </div>

          <div className="movie-grid">
            {feedMovies.map((item) => (
              <MovieCard key={item.id} item={item} />
            ))}
          </div>

          {/* Infinite Scroll Sentinel for Continuous Feed */}
          {feedPage < feedTotalPages && (
            <div ref={feedSentinelRef} style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "40px 0" }}>
              <div className="infinite-scroll-spinner" />
              <span style={{ fontSize: "13px", color: "#94a3b8", marginTop: "10px", fontWeight: "600" }}>
                Auto-loading more movies & series...
              </span>
            </div>
          )}

          {feedPage >= feedTotalPages && feedMovies.length > 0 && (
            <div style={{ textAlign: "center", padding: "50px 0", color: "#64748b", fontSize: "13px", fontWeight: "600" }}>
              ✨ You have reached the end of all {feedTotalItems} titles!
            </div>
          )}
        </div>
      )}

      {/* Floating Back to Top Button */}
      {showScrollTop && (
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="floating-back-to-top"
          title="Back to Top"
          aria-label="Back to Top"
        >
          <ArrowUp size={20} />
        </button>
      )}
    </div>
  );
}
