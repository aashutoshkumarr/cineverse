import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import ErrorBoundary from "./components/ErrorBoundary";
import HomePage from "./pages/HomePage";
import SearchPage from "./pages/SearchPage";
import WatchPage from "./pages/WatchPage";
import WatchlistPage from "./pages/WatchlistPage";
import HistoryPage from "./pages/HistoryPage";

function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [pathname]);

  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <Navbar />
        
        <main style={{ flex: 1 }}>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/watch/:id" element={<WatchPage />} />
              <Route path="/movie/:id" element={<WatchPage />} />
              <Route path="/tv/:id" element={<WatchPage />} />
              <Route path="/watchlist" element={<WatchlistPage />} />
              <Route path="/history" element={<HistoryPage />} />
            </Routes>
          </ErrorBoundary>
        </main>

        <footer style={{ background: "#020916", borderTop: "1px solid rgba(255,255,255,0.06)", padding: "30px 0", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
          <div className="container">
            <p style={{ color: "#ffffff", fontWeight: "800", marginBottom: "6px", fontSize: "15px", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px" }}>
              <img src="/cineverse-card.png" alt="Cineverse" style={{ width: "20px", height: "20px", borderRadius: "5px" }} />
              <span>Cineverse — Your Universe of Entertainment</span>
            </p>
            <p>
              Next-Gen Cinema Streaming & AI Recommendation Platform • High-Speed CDN Playback • Multi-Server Redundancy
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
