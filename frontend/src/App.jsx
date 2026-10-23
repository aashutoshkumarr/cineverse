import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import HomePage from "./pages/HomePage";
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
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/watch/:id" element={<WatchPage />} />
            <Route path="/movie/:id" element={<WatchPage />} />
            <Route path="/tv/:id" element={<WatchPage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>

        <footer style={{ background: "#020916", borderTop: "1px solid rgba(255,255,255,0.06)", padding: "30px 0", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
          <div className="container">
            <p style={{ color: "#94a3b8", fontWeight: "600", marginBottom: "6px" }}>
              🎬 MovieRecommender — Full-Stack Cinema Streaming & AI Recommendation Platform
            </p>
            <p>
              Powered by FastAPI Backend, React 19 Frontend, TMDB Catalog, ML Cosine Similarity, and Multi-Server Streaming.
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
