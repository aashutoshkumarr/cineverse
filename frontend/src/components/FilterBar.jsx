import React from "react";

const COUNTRIES = ["All", "India", "USA", "Japan", "Korea", "China", "UK", "Bangladesh"];
const CATEGORIES = ["All", "Animation", "Anime", "Hindi", "Hollywood", "Telugu", "Tamil", "Malayalam", "K-Drama", "C-Drama"];
const LANGUAGES = ["All", "Hindi", "English"];

export default function FilterBar({
  selectedCountry,
  onSelectCountry,
  selectedCategory,
  onSelectCategory,
  selectedLanguage,
  onSelectLanguage
}) {
  return (
    <div className="filter-section">
      <div className="filter-group">
        <span className="filter-label">Country:</span>
        {COUNTRIES.map((c) => (
          <button
            key={c}
            className={`filter-pill ${selectedCountry === c ? "active" : ""}`}
            onClick={() => onSelectCountry(c)}
          >
            {c}
          </button>
        ))}
      </div>

      <div className="filter-group">
        <span className="filter-label">Category:</span>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            className={`filter-pill ${selectedCategory === cat ? "active" : ""}`}
            onClick={() => onSelectCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="filter-group">
        <span className="filter-label">Language:</span>
        {LANGUAGES.map((l) => (
          <button
            key={l}
            className={`filter-pill ${selectedLanguage === l ? "active" : ""}`}
            onClick={() => onSelectLanguage(l)}
          >
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}
