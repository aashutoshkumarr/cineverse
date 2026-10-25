# 🌌 Cineverse — Your Universe of Entertainment

<div align="center">
  <img src="frontend/public/cineverse-card.png" alt="Cineverse Banner" width="400" style="border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" />
  <br/><br/>
  
  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
  [![Vite](https://img.shields.io/badge/Vite-5.0-646C9A?logo=vite&logoColor=white)](https://vitejs.dev/)
  [![TailwindCSS-Inspired](https://img.shields.io/badge/UI-Modern%20Glassmorphism-ec4899)](#)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
</div>

<p align="center">
  <b>Cineverse</b> is a modern, high-speed, full-stack Cinema Streaming and Content Discovery platform. It blends intelligent Machine Learning recommendations with ultra-fast CDN streaming servers, comprehensive multi-season episode tracking, and a sleek Netflix-style glassmorphic user interface.
</p>

---

## ✨ Features

- ⚡ **Ultra-Fast Instant Playback**: Multi-server CDN redundancy (`vidsrc.su`, `vidlink.pro`, `vidsrc.pm`, `nontongo`) ensures zero-buffer playback without annoying connection failures.
- 📺 **Full TV Series & Season Tracking**: Seamlessly switch between seasons and episodes with authentic poster thumbnails, episode descriptions, and instant stream resolution.
- 🤖 **Hybrid ML Recommender**: Content-based filtering with Cosine Similarity tags mapped to 2,500+ curated catalog titles.
- ♾️ **Infinite Scroll Feed**: Smooth, uninterrupted movie and series browsing with automatic background pre-loading and sleek floating back-to-top controls.
- 🔍 **Modern Pill Search & Dedicated Grid**: Debounced live search with pill capsule controls and instant full-screen search results.
- 💾 **Persistent Server & History Tracking**: Automatically saves your preferred streaming server, resume playback progress, and watchlist locally via SQLite.
- 🎨 **Cosmic Glassmorphic Design**: Modern dark-mode aesthetic with vibrant orange/pink gradients, rounded media badges, and responsive touch controls.

---

## 🏗️ Architecture

```
Movie-Recommender-System/
├── backend/
│   ├── main.py                # FastAPI RESTful API server
│   ├── database.py            # SQLite schema, Watchlist & History persistence
│   ├── recommender.py         # Hybrid ML recommendation engine
│   └── streaming_service.py   # Multi-server CDN router & streaming providers
├── frontend/
│   ├── src/
│   │   ├── components/        # Navbar, MovieCard, HeroBanner, VideoPlayer
│   │   ├── pages/             # HomePage, WatchPage, SearchPage, WatchlistPage
│   │   └── services/api.js    # API client connecting to FastAPI
│   └── public/                # Logos, favicons, branding assets
├── netmirror_catalog.json     # Curated 2,500+ movies & TV series catalog
├── START_CINEVERSE.bat        # 1-Click launcher for Windows
└── requirements.txt           # Python backend dependencies
```

---

## 🚀 Quick Start

### Option 1: One-Click Launcher (Windows)
Simply double click on **`START_CINEVERSE.bat`** in the project directory! It starts both backend and frontend servers and launches Cineverse in your default browser automatically.

---

### Option 2: Manual Setup

#### 1. Clone the repository:
```bash
git clone https://github.com/aashutoshkumarr/movie-recommender-system.git
cd movie-recommender-system
```

#### 2. Backend Setup:
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Start FastAPI Server (Port 8000)
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 3. Frontend Setup:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite Development Server (Port 3001)
npm run dev -- --port 3001
```

Open your browser and navigate to:
👉 **`http://localhost:3001`**

---

## 🛠️ Tech Stack

- **Frontend**: React 18, Vite, Lucide Icons, Modern CSS3 Flexbox/Grid with Glassmorphism
- **Backend**: FastAPI, Uvicorn, Python 3.10+, SQLite3
- **Machine Learning**: Scikit-Learn (Cosine Similarity), Pandas, NumPy
- **Streaming & Metadata**: TMDB API, Multi-Server CDN mirrors

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
