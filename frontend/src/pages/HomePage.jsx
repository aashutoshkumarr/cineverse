import React, { useState, useEffect } from "react";
import HeroBanner from "../components/HeroBanner";
import FilterBar from "../components/FilterBar";
import MovieShelf from "../components/MovieShelf";
import MovieCard from "../components/MovieCard";
import { fetchShelves, fetchMovies } from "../services/api";
import { ChevronLeft, ChevronRight, Compass } from "lucide-react";

export default function HomePage() {
  const [shelves, setShelves] = useState([]);
  const [featured, setFeatured] = useState(null);
  
  // Filters
  const [country, setCountry] = useState("All");
  const [category, setCategory] = useState("All");
  const [language, setLanguage] = useState("All");
  
  // Filtered Results Pagination
  const [filterPage, setFilterPage] = useState(1);
  const [filterData, setFilterData] = useState({ results: [], total_pages: 1, total_items: 0 });
  const [loadingFilter, setLoadingFilter] = useState(false);

  // Home Continuous Feed
  const [homeVisibleCount, setHomeVisibleCount] = useState(48);
  const [allMovies, setAllMovies] = useState([]);

  const isFiltered = country !== "All" || category !== "All" || language !== "All";

  // Load initial shelves and featured movie
  useEffect(() => {
    fetchShelves().then((data) => {
      setShelves(data);
      if (data.length > 0 && data[0].items.length > 0) {
        setFeatured(data[0].items[0]);
      }
    });

    fetchMovies(1, 240, "All", "All", "All").then((data) => {
      setAllMovies(data.results || []);
    });
  }, []);

  // When filters change, reset page to 1 and fetch
  useEffect(() => {
    if (!isFiltered) return;
    setLoadingFilter(true);
    fetchMovies(filterPage, 24, country, category, language)
      .then((data) => {
        setFilterData(data);
      })
      .finally(() => setLoadingFilter(false));
  }, [country, category, language, filterPage, isFiltered]);

  const handleCountryChange = (c) => {
    setCountry(c);
    setFilterPage(1);
  };
  const handleCategoryChange = (cat) => {
    setCategory(cat);
    setFilterPage(1);
  };
  const handleLanguageChange = (l) => {
    setLanguage(l);
    setFilterPage(1);
  };

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

      {/* If Filter is Active: Show Filtered Grid with Page Navigation */}
      {isFiltered ? (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <h2 style={{ fontSize: "22px", fontWeight: "800" }}>
              📍 Filter Results: <span style={{ color: "#38bdf8" }}>{country} • {category} • {language}</span>
            </h2>
            <span style={{ color: "#94a3b8", fontSize: "14px" }}>
              Showing {filterData.results.length} of {filterData.total_items} titles
            </span>
          </div>

          {loadingFilter ? (
            <div style={{ textAlign: "center", padding: "60px 0", color: "#94a3b8" }}>
              Loading movies...
            </div>
          ) : filterData.results.length > 0 ? (
            <>
              <div className="movie-grid">
                {filterData.results.map((item) => (
                  <MovieCard key={item.id} item={item} />
                ))}
              </div>

              {/* Bidirectional Pagination */}
              <div className="pagination-bar">
                <button
                  className="page-btn"
                  disabled={filterPage <= 1}
                  onClick={() => setFilterPage((p) => Math.max(1, p - 1))}
                >
                  <ChevronLeft size={18} /> Previous Page
                </button>
                <div className="page-info">
                  📄 Page {filterPage} of {filterData.total_pages}
                </div>
                <button
                  className="page-btn"
                  disabled={filterPage >= filterData.total_pages}
                  onClick={() => setFilterPage((p) => p + 1)}
                >
                  Next Page <ChevronRight size={18} />
                </button>
              </div>
            </>
          ) : (
            <div style={{ textAlign: "center", padding: "60px 20px", background: "rgba(255,255,255,0.02)", borderRadius: "16px" }}>
              <h3>No titles found for this filter</h3>
              <p style={{ color: "#94a3b8", marginTop: "8px" }}>Try selecting "All" or a different combination.</p>
            </div>
          )}
        </div>
      ) : (
        /* If No Filter is Active: Show 11 Curated Shelves + Continuous Discovery Feed */
        <div>
          {shelves.map((shelf) => (
            <MovieShelf key={shelf.id} shelf={shelf} />
          ))}

          {/* Continuous Discovery Feed */}
          <div style={{ marginTop: "60px", marginBottom: "25px", borderBottom: "2px solid rgba(255,255,255,0.06)", paddingBottom: "14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "22px", fontWeight: "800", display: "flex", alignItems: "center", gap: "10px" }}>
              <Compass color="#f97316" />
              <span>Continuous Discovery Feed</span>
              <span className="badge-counter" style={{ fontSize: "13px" }}>2,490+ Titles Available</span>
            </h2>
            <span style={{ color: "#94a3b8", fontSize: "14px" }}>
              Scroll down to explore all movies & series
            </span>
          </div>

          <div className="movie-grid">
            {allMovies.slice(0, homeVisibleCount).map((item) => (
              <MovieCard key={item.id} item={item} />
            ))}
          </div>

          <div style={{ display: "flex", justifyContent: "center", gap: "16px", margin: "30px 0" }}>
            {homeVisibleCount < allMovies.length && (
              <button
                className="btn-primary"
                onClick={() => setHomeVisibleCount((c) => c + 48)}
              >
                ⬇️ Load More Titles (Showing {Math.min(homeVisibleCount, allMovies.length)} of {allMovies.length})
              </button>
            )}
            {homeVisibleCount > 48 && (
              <button
                className="btn-secondary"
                onClick={() => {
                  setHomeVisibleCount(48);
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
              >
                ⬆️ Back to Top
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
