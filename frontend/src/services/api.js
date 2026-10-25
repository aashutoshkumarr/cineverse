const API_BASE = "http://127.0.0.1:8000/api";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchMovies(page = 1, limit = 24, country = "All", category = "All", language = "All") {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(limit),
    country,
    category,
    language
  });
  const res = await fetch(`${API_BASE}/movies?${params}`);
  return res.json();
}

export async function fetchShelves() {
  const res = await fetch(`${API_BASE}/shelves`);
  return res.json();
}

export async function searchMovies(q) {
  const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
  return res.json();
}

export async function fetchMovieDetail(id, type = "", s = 1, e = 1) {
  const typeQuery = (type && type !== "null" && type !== "undefined") ? `&type=${type}` : "";
  const res = await fetch(`${API_BASE}/movie/${id}?s=${s}&e=${e}${typeQuery}`);
  return res.json();
}

export async function fetchRecommendations(id, title) {
  const params = new URLSearchParams();
  if (title) params.append("title", title);
  const res = await fetch(`${API_BASE}/recommend/${id}?${params}`);
  return res.json();
}

export async function fetchWatchlist() {
  const res = await fetch(`${API_BASE}/watchlist`);
  return res.json();
}

export async function addToWatchlist(item) {
  const res = await fetch(`${API_BASE}/watchlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(item)
  });
  return res.json();
}

export async function removeFromWatchlist(id) {
  const res = await fetch(`${API_BASE}/watchlist/${id}`, { method: "DELETE" });
  return res.json();
}

export async function fetchHistory() {
  const res = await fetch(`${API_BASE}/history`);
  return res.json();
}

export async function addToHistory(item) {
  const res = await fetch(`${API_BASE}/history`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(item)
  });
  return res.json();
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
