// Dynamic API Base URL: Uses VITE_API_BASE_URL if configured, otherwise falls back to current hostname on port 8000
const getApiBase = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window !== "undefined" && window.location && window.location.hostname) {
    // If accessing via local IP (e.g. 192.168.x.x or phone), connect to backend on same host
    return `http://${window.location.hostname}:8000/api`;
  }
  return "http://127.0.0.1:8000/api";
};

const API_BASE = getApiBase();

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("Health check failed");
    return await res.json();
  } catch (err) {
    console.error("fetchHealth error:", err);
    return { status: "offline", total_catalog: 0 };
  }
}

export async function fetchMovies(page = 1, limit = 24, country = "All", category = "All", language = "All") {
  try {
    const params = new URLSearchParams({
      page: String(page),
      limit: String(limit),
      country,
      category,
      language
    });
    const res = await fetch(`${API_BASE}/movies?${params}`);
    if (!res.ok) throw new Error("Failed to fetch movies");
    return await res.json();
  } catch (err) {
    console.error("fetchMovies error:", err);
    return { results: [], total: 0, page, has_more: false };
  }
}

export async function fetchShelves() {
  try {
    const res = await fetch(`${API_BASE}/shelves`);
    if (!res.ok) throw new Error("Failed to fetch shelves");
    return await res.json();
  } catch (err) {
    console.error("fetchShelves error:", err);
    return [];
  }
}

export async function searchMovies(q) {
  try {
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) throw new Error("Search failed");
    return await res.json();
  } catch (err) {
    console.error("searchMovies error:", err);
    return { results: [], count: 0 };
  }
}

export async function fetchMovieDetail(id, type = "", s = 1, e = 1) {
  try {
    const typeQuery = (type && type !== "null" && type !== "undefined") ? `&type=${type}` : "";
    const res = await fetch(`${API_BASE}/movie/${id}?s=${s}&e=${e}${typeQuery}`);
    if (!res.ok) throw new Error("Failed to fetch movie detail");
    return await res.json();
  } catch (err) {
    console.error("fetchMovieDetail error:", err);
    return null;
  }
}

export async function fetchRecommendations(id, title) {
  try {
    const params = new URLSearchParams();
    if (title) params.append("title", title);
    const res = await fetch(`${API_BASE}/recommend/${id}?${params}`);
    if (!res.ok) throw new Error("Failed to fetch recommendations");
    return await res.json();
  } catch (err) {
    console.error("fetchRecommendations error:", err);
    return [];
  }
}

export async function fetchWatchlist() {
  try {
    const res = await fetch(`${API_BASE}/watchlist`);
    if (!res.ok) throw new Error("Failed to fetch watchlist");
    return await res.json();
  } catch (err) {
    console.error("fetchWatchlist error:", err);
    return [];
  }
}

export async function addToWatchlist(item) {
  try {
    const res = await fetch(`${API_BASE}/watchlist`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(item)
    });
    return await res.json();
  } catch (err) {
    console.error("addToWatchlist error:", err);
    return null;
  }
}

export async function removeFromWatchlist(id) {
  try {
    const res = await fetch(`${API_BASE}/watchlist/${id}`, { method: "DELETE" });
    return await res.json();
  } catch (err) {
    console.error("removeFromWatchlist error:", err);
    return null;
  }
}

export async function fetchHistory() {
  try {
    const res = await fetch(`${API_BASE}/history`);
    if (!res.ok) throw new Error("Failed to fetch history");
    return await res.json();
  } catch (err) {
    console.error("fetchHistory error:", err);
    return [];
  }
}

export async function addToHistory(item) {
  try {
    const res = await fetch(`${API_BASE}/history`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(item)
    });
    return await res.json();
  } catch (err) {
    console.error("addToHistory error:", err);
    return null;
  }
}

export async function updatePlaybackProgress(tmdbId, progressSeconds, durationSeconds) {
  try {
    const res = await fetch(`${API_BASE}/history/${tmdbId}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        progress_seconds: progressSeconds,
        duration_seconds: durationSeconds
      })
    });
    return res.json();
  } catch (e) {
    return null;
  }
}

export async function clearHistory() {
  const res = await fetch(`${API_BASE}/history`, { method: "DELETE" });
  return res.json();
}
