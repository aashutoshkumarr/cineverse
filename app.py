import streamlit as st
import pickle
import pandas as pd
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import api_service as api

# -----------------------------
# Streamlit Config
# -----------------------------
st.set_page_config(
    page_title="MovieRecommender – Watch & Discover Movies",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# Session State Initialization
# -----------------------------
if "watch_history" not in st.session_state:
    st.session_state.watch_history = []
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "show_history" not in st.session_state:
    st.session_state.show_history = False
if "show_watchlist" not in st.session_state:
    st.session_state.show_watchlist = False
if "page_offset" not in st.session_state:
    st.session_state.page_offset = 1
if "home_visible_count" not in st.session_state:
    st.session_state.home_visible_count = 48

# -----------------------------
# Stylesheet
# -----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
        background-color: #041226 !important;
        color: #ffffff;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 4rem !important;
        max-width: 1400px !important;
    }

    #MainMenu, header, footer {
        visibility: hidden !important;
        height: 0px !important;
    }

    /* Top Navbar */
    .nm-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 10px;
        margin-bottom: 12px;
    }
    .nm-logo-container {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .nm-logo {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
    }
    .nm-logo-green {
        color: #00e676;
        text-shadow: 0 0 20px rgba(0, 230, 118, 0.5);
    }
    .nm-api-badges {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .nm-api-pill {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #94a3b8;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 12px;
    }

    /* Search Bar Input */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        border-radius: 30px !important;
        padding: 12px 24px !important;
        border: none !important;
        line-height: 1.5 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #94a3b8 !important;
        font-size: 15px !important;
        line-height: normal !important;
    }

    /* Red-Orange Search Button */
    div.stButton > button {
        background: linear-gradient(90deg, #f97316 0%, #ef4444 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        border-radius: 30px !important;
        border: none !important;
        box-shadow: 0 4px 18px rgba(239, 68, 68, 0.45) !important;
        transition: all 0.25s ease !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.65) !important;
    }

    /* Filter Labels & Arrows */
    .nm-filter-title {
        font-size: 15px;
        font-weight: 600;
        color: #cbd5e1;
        margin: 10px 0 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .nm-arrow {
        width: 22px;
        height: 22px;
        background: rgba(255, 255, 255, 0.12);
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        color: #ffffff;
    }

    /* Filter Pills */
    .stPills button {
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        color: #e2e8f0 !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 5px 16px !important;
        transition: all 0.2s !important;
    }
    .stPills button:hover {
        border-color: #f97316 !important;
        color: #f97316 !important;
    }
    .stPills button[aria-selected="true"] {
        background: #f97316 !important;
        border-color: #f97316 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Shelf Header */
    .nm-shelf-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 28px 0 16px;
    }
    .nm-shelf-title {
        font-size: 21px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.3px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .nm-view-all-btn {
        background: linear-gradient(90deg, #f97316, #ef4444);
        color: #ffffff;
        font-size: 13px;
        font-weight: 700;
        padding: 5px 16px;
        border-radius: 20px;
        border: none;
        cursor: pointer;
    }

    /* Poster Card */
    .nm-card-container {
        display: flex;
        flex-direction: column;
        width: 100%;
        margin-bottom: 22px;
        transition: transform 0.25s ease;
    }
    .nm-card-container:hover {
        transform: translateY(-6px);
    }
    .nm-poster-box {
        position: relative;
        width: 100%;
        aspect-ratio: 2 / 3;
        border-radius: 12px;
        overflow: hidden;
        background: #020916;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.5);
    }
    .nm-poster-box img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }
    .nm-top-badge {
        position: absolute;
        top: 6px;
        right: 6px;
        background: #e11d48;
        color: #ffffff;
        font-size: 10px;
        font-weight: 800;
        padding: 2px 7px;
        border-radius: 4px;
        letter-spacing: 0.3px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
    }
    .nm-rating-circle {
        position: absolute;
        bottom: 8px;
        left: 8px;
        width: 34px;
        height: 34px;
        background: #ffffff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 800;
        color: #0f172a;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
    }
    .nm-circle-green {
        border: 2.5px solid #22c55e;
    }
    .nm-circle-yellow {
        border: 2.5px solid #f59e0b;
    }
    .nm-circle-orange {
        border: 2.5px solid #f97316;
    }
    .nm-title-text {
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
        margin-top: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3;
    }
    .nm-year-text {
        font-size: 12px;
        color: #64748b;
        margin-top: 2px;
    }

    /* OTT Streaming Banner */
    .nm-stream-badge {
        background: rgba(0, 230, 118, 0.12);
        color: #00e676;
        border: 1px solid rgba(0, 230, 118, 0.3);
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Top Navbar
# -----------------------------
nav_col1, nav_col2 = st.columns([6, 4])
with nav_col1:
    st.markdown("""
    <div class="nm-logo-container">
        <span class="nm-logo">Movie<span class="nm-logo-green">Recommender</span></span>
        <div class="nm-api-badges">
            <span class="nm-api-pill">TMDB Dynamic</span>
            <span class="nm-api-pill">TVmaze</span>
            <span class="nm-api-pill">AniList</span>
            <span class="nm-api-pill">Watchmode</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with nav_col2:
    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button(f"⭐ Watchlist ({len(st.session_state.watchlist)})"):
            st.session_state.show_watchlist = not st.session_state.show_watchlist
    with btn2:
        if st.button(f"🕒 History ({len(st.session_state.watch_history)})"):
            st.session_state.show_history = not st.session_state.show_history

# -----------------------------
# Watchlist & History Drawers
# -----------------------------
if st.session_state.show_watchlist:
    with st.expander("⭐ Your Personal Watchlist", expanded=True):
        if st.session_state.watchlist:
            w_cols = st.columns(min(len(st.session_state.watchlist), 6))
            for idx, item in enumerate(st.session_state.watchlist[::-1]):
                with w_cols[idx % 6]:
                    st.image(item.get("poster"), width=120)
                    st.caption(f"{item.get('title')} ({item.get('year')})")
            if st.button("Clear Watchlist"):
                st.session_state.watchlist = []
                st.rerun()
        else:
            st.info("Your watchlist is empty! Click 'Add to Watchlist' on any title.")

if st.session_state.show_history:
    with st.expander("🕒 Recent Watch & Search History", expanded=True):
        if st.session_state.watch_history:
            h_cols = st.columns(min(len(st.session_state.watch_history), 6))
            for idx, hist in enumerate(st.session_state.watch_history[-6:][::-1]):
                with h_cols[idx % 6]:
                    st.image(hist.get("poster"), width=120)
                    st.caption(f"{hist.get('title')} ({hist.get('year')})")
            if st.button("Clear History"):
                st.session_state.watch_history = []
                st.rerun()
        else:
            st.info("No watch history yet.")

# -----------------------------
# Base Catalog Loading
# -----------------------------
@st.cache_data(show_spinner=False)
def load_base_catalog():
    with open('netmirror_catalog.json', 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    return catalog

catalog = load_base_catalog()

# -----------------------------
# Cached API Wrappers (1 Hour TTL for fast loads)
# -----------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def search_tmdb_cached(q):
    return api.search_tmdb_multi(q)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_tmdb_recs_cached(media_type, media_id):
    return api.fetch_tmdb_recommendations(media_type, media_id)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_streaming_cached(media_type, media_id):
    return api.fetch_streaming_providers(media_type, media_id, "IN")

@st.cache_data(ttl=3600, show_spinner=False)
def discover_tmdb_cached(country, category, language, page=1):
    return api.fetch_tmdb_discover(country, category, language, page)

@st.cache_data(ttl=3600, show_spinner=False)
def anilist_trending_cached(page=1, per_page=12):
    return api.fetch_anilist_trending(page, per_page)

# -----------------------------
# Search Bar
# -----------------------------
search_wrapper_l, search_wrapper_c, search_wrapper_r = st.columns([1, 7, 1])

with search_wrapper_c:
    s_col1, s_col2 = st.columns([5, 1])
    with s_col1:
        search_query = st.text_input(
            "Search Input",
            placeholder="Search ANY movie, cartoon, anime or series.. (e.g. Doraemon, Squid Game, Avatar, Animal)",
            label_visibility="collapsed"
        )
    with s_col2:
        search_button = st.button("Search")

# -----------------------------
# Filter Bars (Country, Category, Language)
# -----------------------------
filter_col_l, filter_col_m, filter_col_r = st.columns([1, 9, 1])
with filter_col_m:
    st.markdown("""
    <div class="nm-filter-title">
        <span>Country</span>
        <span class="nm-arrow">&lt;</span>
        <span class="nm-arrow">&gt;</span>
    </div>
    """, unsafe_allow_html=True)
    country_choice = st.pills(
        "Country Filter",
        options=["All", "India", "USA", "Japan", "Korea", "China", "UK", "Bangladesh"],
        default="All",
        label_visibility="collapsed"
    )

    st.markdown("""
    <div class="nm-filter-title">
        <span>Category</span>
        <span class="nm-arrow">&lt;</span>
        <span class="nm-arrow">&gt;</span>
    </div>
    """, unsafe_allow_html=True)
    category_choice = st.pills(
        "Category Filter",
        options=["All", "Animation", "Anime", "Hindi", "Hollywood", "Telugu", "Tamil", "Malayalam", "K-Drama", "C-Drama"],
        default="All",
        label_visibility="collapsed"
    )

    lang_choice = st.pills(
        "Language Filter",
        options=["All", "Hindi", "English"],
        default="All",
        label_visibility="collapsed"
    )

    # Track filter changes to automatically reset pagination to Page 1
    current_filter_sig = f"{country_choice}_{category_choice}_{lang_choice}"
    if "last_filter_sig" not in st.session_state:
        st.session_state.last_filter_sig = current_filter_sig
    elif st.session_state.last_filter_sig != current_filter_sig:
        st.session_state.page_offset = 1
        st.session_state.last_filter_sig = current_filter_sig

# -----------------------------
# Renderers
# -----------------------------
def render_shelf(items, shelf_title, show_view_all=True, badge_tag=""):
    st.markdown(f"""
    <div class="nm-shelf-header">
        <span class="nm-shelf-title">
            <span>{shelf_title}</span>
            {f'<span class="nm-api-pill">{badge_tag}</span>' if badge_tag else ''}
        </span>
        {'<button class="nm-view-all-btn">View All</button>' if show_view_all else ''}
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(min(len(items), 7))
    for i, item in enumerate(items[:7]):
        rating = float(item.get('rating', 7.5))
        border_class = "nm-circle-green" if rating >= 7.5 else ("nm-circle-yellow" if rating >= 6.4 else "nm-circle-orange")
        badge_text = item.get('badge', 'HD')
        title = item.get('title', 'Movie')
        fallback_uri = api.get_svg_fallback(title, item.get('category', 'Movie'))
        poster_src = item.get('poster') or fallback_uri

        with cols[i]:
            st.markdown(f"""
            <div class="nm-card-container">
                <div class="nm-poster-box">
                    <img src="{poster_src}" alt="{title}" onerror="this.onerror=null; this.src='{fallback_uri}';" />
                    <span class="nm-top-badge">{badge_text}</span>
                    <div class="nm-rating-circle {border_class}">{rating:.1f}</div>
                </div>
                <div class="nm-title-text" title="{title}">{title}</div>
                <div class="nm-year-text">{item.get('year', '2024')}</div>
            </div>
            """, unsafe_allow_html=True)

def render_grid(items, title):
    st.markdown(f"""
    <div class="nm-shelf-header">
        <span class="nm-shelf-title">{title}</span>
    </div>
    """, unsafe_allow_html=True)

    num_cols = 6
    for row_start in range(0, len(items), num_cols):
        row_items = items[row_start:row_start + num_cols]
        cols = st.columns(num_cols)
        for i, item in enumerate(row_items):
            rating = float(item.get('rating', 7.5))
            border_class = "nm-circle-green" if rating >= 7.5 else ("nm-circle-yellow" if rating >= 6.4 else "nm-circle-orange")
            badge_text = item.get('badge', 'HD')
            title = item.get('title', 'Movie')
            fallback_uri = api.get_svg_fallback(title, item.get('category', 'Movie'))
            poster_src = item.get('poster') or fallback_uri

            with cols[i]:
                st.markdown(f"""
                <div class="nm-card-container">
                    <div class="nm-poster-box">
                        <img src="{poster_src}" alt="{title}" onerror="this.onerror=null; this.src='{fallback_uri}';" />
                        <span class="nm-top-badge">{badge_text}</span>
                        <div class="nm-rating-circle {border_class}">{rating:.1f}</div>
                    </div>
                    <div class="nm-title-text" title="{title}">{title}</div>
                    <div class="nm-year-text">{item.get('year', '2024')}</div>
                </div>
                """, unsafe_allow_html=True)

# -----------------------------
# 🎯 DYNAMIC LIVE SEARCH (TMDB API Multi-Search + Recommendations)
# -----------------------------
if search_query and search_query.strip():
    clean_q = search_query.strip()
    with st.spinner(f"Searching TMDB live catalog for '{clean_q}'..."):
        # 1. Query TMDB Live Search
        live_results = search_tmdb_cached(clean_q)

        # 2. Fallback to local catalog if empty
        if not live_results:
            live_results = [c for c in catalog if clean_q.lower() in c['clean_title'].lower() or clean_q.lower() in c['title'].lower()]

        if live_results:
            top_match = live_results[0]
            m_id = top_match.get("id")
            m_type = top_match.get("media_type", "movie")

            # Record into watch history
            if not any(h.get('title') == top_match.get('title') for h in st.session_state.watch_history):
                st.session_state.watch_history.append(top_match)

            # Streaming Availability
            providers = fetch_streaming_cached(m_type, m_id)
            prov_str = ", ".join(providers) if providers else "Netflix, JioHotstar, Prime Video"

            # Top Match Hero Card with Synopsis & Watchlist Button
            card_col_img, card_col_info = st.columns([1, 4])
            with card_col_img:
                st.image(top_match.get("poster"), width=180)
            with card_col_info:
                st.markdown(f"### {top_match.get('title')} ({top_match.get('year')})")
                st.markdown(f"⭐ **Rating:** {top_match.get('rating')}/10 • **Type:** {m_type.upper()}")
                st.markdown(f"*{top_match.get('overview', 'No overview provided.')}*")
                st.markdown(f"<div class='nm-stream-badge'>📺 Available on: <b>{prov_str}</b></div>", unsafe_allow_html=True)

                if st.button("➕ Add to Watchlist"):
                    if not any(w.get('title') == top_match.get('title') for w in st.session_state.watchlist):
                        st.session_state.watchlist.append(top_match)
                        st.success(f"Added {top_match.get('title')} to your Watchlist!")
                    else:
                        st.info("Already in your Watchlist!")

            # Live TMDB Recommendations for this exact title
            recs = fetch_tmdb_recs_cached(m_type, m_id)
            if not recs:
                recs = live_results[1:] if len(live_results) > 1 else catalog[:7]

            render_shelf(recs, f"🎯 Recommendations based on '{top_match.get('title')}'", show_view_all=False, badge_tag="TMDB AI Match")
        else:
            st.warning(f"No results found for '{clean_q}'. Try another title or explore by Country & Category below.")

# -----------------------------
# 🎯 DYNAMIC FILTERING (TMDB Discover + Local Catalog)
# -----------------------------
is_country_filtered = (country_choice and country_choice != "All")
is_category_filtered = (category_choice and category_choice != "All")
is_lang_filtered = (lang_choice and lang_choice != "All")

is_any_filter_active = is_country_filtered or is_category_filtered or is_lang_filtered

if is_any_filter_active:
    filtered_results = catalog.copy()

    if is_country_filtered:
        filtered_results = [m for m in filtered_results if m.get('country') == country_choice]
    if is_category_filtered:
        filtered_results = [m for m in filtered_results if m.get('category') == category_choice]
    if is_lang_filtered:
        filtered_results = [m for m in filtered_results if lang_choice in m.get('languages', [m.get('language')])]

    # Supplement dynamically from TMDB Discover API
    try:
        live_discover = discover_tmdb_cached(country_choice, category_choice, lang_choice, page=st.session_state.page_offset)
        for item in live_discover:
            if not any(f['clean_title'].lower() == item['clean_title'].lower() for f in filtered_results):
                filtered_results.append(item)
    except Exception:
        pass

    # Header
    title_parts = []
    if is_country_filtered:
        title_parts.append(f"{country_choice}")
    if is_category_filtered:
        title_parts.append(f"{category_choice}")
    if is_lang_filtered:
        title_parts.append(f"({lang_choice})")

    filter_heading = "📍 Results for " + " • ".join(title_parts)

    if filtered_results:
        # Page Slicing (24 titles per page for lightning fast rendering)
        PAGE_SIZE = 24
        total_items = len(filtered_results)
        total_pages = max(1, (total_items + PAGE_SIZE - 1) // PAGE_SIZE)

        if st.session_state.page_offset > total_pages:
            st.session_state.page_offset = total_pages
        if st.session_state.page_offset < 1:
            st.session_state.page_offset = 1

        start_idx = (st.session_state.page_offset - 1) * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, total_items)
        page_items = filtered_results[start_idx:end_idx]

        render_grid(page_items, f"{filter_heading} &nbsp;•&nbsp; <span style='font-size:14px; color:#94a3b8; font-weight:normal;'>Showing {start_idx + 1}–{end_idx} of {total_items} titles</span>")

        # Bidirectional Pagination Controls (Previous / Current Page / Next Page)
        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        with p_col1:
            if st.session_state.page_offset > 1:
                if st.button("⬅️ Previous Page", use_container_width=True):
                    st.session_state.page_offset -= 1
                    st.rerun()
            else:
                st.button("⬅️ Previous Page", disabled=True, use_container_width=True)
        with p_col2:
            st.markdown(
                f"<div style='text-align: center; color: #94a3b8; font-weight: 600; line-height: 42px; font-size: 15px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);'>"
                f"📄 Page {st.session_state.page_offset} of {total_pages}"
                f"</div>",
                unsafe_allow_html=True
            )
        with p_col3:
            if st.session_state.page_offset < total_pages:
                if st.button("Next Page ➡️", use_container_width=True):
                    st.session_state.page_offset += 1
                    st.rerun()
            else:
                st.button("Next Page ➡️", disabled=True, use_container_width=True)
    else:
        st.markdown(f"""
        <div style="text-align: center; padding: 60px 20px; background: rgba(255, 255, 255, 0.02); border-radius: 16px; margin-top: 30px; border: 1px dashed rgba(255, 255, 255, 0.1);">
            <div style="font-size: 48px; margin-bottom: 12px;">🔍</div>
            <h3 style="color: #ffffff; font-size: 20px; margin-bottom: 8px;">No titles found for {filter_heading}</h3>
            <p style="color: #94a3b8; font-size: 14px;">Try selecting 'All' or a different category to explore thousands of titles.</p>
        </div>
        """, unsafe_allow_html=True)

else:
    # -----------------------------
    # Home Page (When all filters are "All")
    # -----------------------------
    # 1. Trending Now
    render_shelf(catalog[:7], "Trending Now - MovieRecommender", badge_tag="TMDB Popular")

    # 2. Cartoons & Kids Favorites
    cartoons = [m for m in catalog if m.get('category') == 'Animation']
    if cartoons:
        render_shelf(cartoons, "🧸 Cartoons & Kids Favorites (Doraemon, Chhota Bheem, Tom & Jerry)", badge_tag="Cartoons")

    # 3. Top Anime (Live AniList GraphQL API)
    try:
        live_anime = anilist_trending_cached(page=1, per_page=7)
    except Exception:
        live_anime = []
    anime_items = live_anime if live_anime else [m for m in catalog if m.get('category') == 'Anime']
    render_shelf(anime_items, "⚔️ Top Anime & Japanese Animation (Powered by AniList)", badge_tag="AniList Live")

    # 4. K-Dramas & Asian Series (Live TMDB Discover)
    try:
        live_kdrama = discover_tmdb_cached("Korea", "K-Drama", "All", page=1)[:7]
    except Exception:
        live_kdrama = []
    kdrama_items = live_kdrama if live_kdrama else [m for m in catalog if m.get('country') == 'Korea']
    render_shelf(kdrama_items, "🇰🇷 Top K-Dramas & Korean Cinema (Squid Game, Crash Landing)", badge_tag="TMDB + TVmaze")

    # 5. Indian Mega Blockbusters & Bollywood
    hindi_items = [m for m in catalog if m.get('country') == 'India' and m.get('category') == 'Hindi']
    if hindi_items:
        render_shelf(hindi_items[:7], "🇮🇳 Bollywood & Hindi Cinema Hits", badge_tag="Bollywood")

    # 6. South Indian Pan-India Blockbusters (Tollywood, Kollywood, Mollywood)
    south_items = [m for m in catalog if m.get('country') == 'India' and m.get('category') in ['Telugu', 'Tamil', 'Malayalam']]
    if south_items:
        render_shelf(south_items[:7], "🏹 South Indian Pan-India Action (Tollywood, Kollywood, Mollywood)", badge_tag="South Action")

    # 7. Hollywood Blockbusters
    hollywoods = [m for m in catalog if m.get('country') == 'USA' and m.get('category') == 'Hollywood']
    if hollywoods:
        render_shelf(hollywoods[:7], "🇺🇸 Hollywood & Western Blockbusters", badge_tag="Hollywood")

    # 8. All-Time Hall of Fame (Top Rated 8.0+)
    top_rated_items = [m for m in catalog if float(m.get('rating', 0)) >= 8.2]
    if top_rated_items:
        render_shelf(top_rated_items[:7], "⭐ Hall of Fame: All-Time Masterpieces (Rating 8.2+)", badge_tag="IMDb / TMDB Gold")

    # 9. Chinese Cinema & C-Dramas
    chinese = [m for m in catalog if m.get('country') == 'China']
    if chinese:
        render_shelf(chinese[:7], "🇨🇳 Chinese Cinema & C-Dramas", badge_tag="C-Drama")

    # 10. UK British Cinema & Crime
    uk_items = [m for m in catalog if m.get('country') == 'UK']
    if uk_items:
        render_shelf(uk_items[:7], "🇬🇧 British Classics & Crime Series", badge_tag="BBC & UK")

    # 11. Bangladeshi Cinema & Hits
    bangla_items = [m for m in catalog if m.get('country') == 'Bangladesh']
    if bangla_items:
        render_shelf(bangla_items[:7], "🇧🇩 Bangladeshi Cinema & Hits", badge_tag="Bengali Cinema")

    # -----------------------------
    # 12. Continuous Endless Discovery Feed (NetMirror Style)
    # -----------------------------
    st.markdown("""
    <div style="margin-top: 60px; margin-bottom: 25px; padding-bottom: 12px; border-bottom: 2px solid rgba(255,255,255,0.06); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <span style="font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;">
            🌐 Continuous Discovery Feed <span class="nm-api-pill" style="margin-left: 10px;">2,490+ Titles Available</span>
        </span>
        <span style="color: #94a3b8; font-size: 14px; font-weight: 500;">
            Scroll & load unlimited movies and series below
        </span>
    </div>
    """, unsafe_allow_html=True)

    visible_home_items = catalog[:st.session_state.home_visible_count]
    render_grid(visible_home_items, "")

    # Load More Button
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    h_col1, h_col2, h_col3 = st.columns([1, 2, 1])
    with h_col2:
        if st.session_state.home_visible_count < len(catalog):
            if st.button(
                f"⬇️ Load More Titles (Showing {min(st.session_state.home_visible_count, len(catalog))} of {len(catalog)})",
                key="home_load_more_btn",
                use_container_width=True
            ):
                st.session_state.home_visible_count += 48
                st.rerun()
        else:
            st.info("🎉 You have reached the end of the entire 2,490+ movie catalog!")

    with h_col3:
        if st.session_state.home_visible_count > 48:
            if st.button("⬆️ Reset to Top", key="home_reset_btn", use_container_width=True):
                st.session_state.home_visible_count = 48
                st.rerun()

# -----------------------------
# Footer
# -----------------------------
st.markdown("""
<div style="margin-top: 60px; padding: 25px 0; border-top: 1px solid rgba(255,255,255,0.08); text-align: center; color: #64748b; font-size: 13px;">
    <p style="color: #94a3b8; font-weight: 500;">MovieRecommender is powered dynamically by TMDB API, TVmaze API, AniList GraphQL, and Watchmode availability.</p>
    <p>© 2026 MovieRecommender. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)
