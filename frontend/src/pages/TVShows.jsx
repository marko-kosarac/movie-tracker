import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import TVShowCard from "../components/TVShowCard";
import { API_URL } from "../config";
import "./Movies.css";

function TVShows() {
  const [tvShows, setTvShows] = useState([]);

  const [selectedGenre, setSelectedGenre] = useState(
    sessionStorage.getItem("tvShowsGenre") || "Recommended"
  );

  const [sort, setSort] = useState(
    sessionStorage.getItem("tvShowsSort") || "rating"
  );

  const [loading, setLoading] = useState(true);

  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const searchTerm = queryParams.get("search") || "";

  const tabsRef = useRef(null);

  const genres = [
    "Recommended",
    "Action & Adventure",
    "Drama",
    "Comedy",
    "Crime",
    "Mystery",
    "Sci-Fi & Fantasy",
    "Animation",
    "Family",
    "Documentary",
  ];

  const scrollGenres = (direction) => {
    if (tabsRef.current) {
      tabsRef.current.scrollBy({
        left: direction === "left" ? -300 : 300,
        behavior: "smooth",
      });
    }
  };

  const sortRecommendedShows = (data) => {
    const finalData = [...data];

    if (sort === "year_desc") {
      finalData.sort((a, b) => b.year - a.year);
    } else if (sort === "year_asc") {
      finalData.sort((a, b) => a.year - b.year);
    } else if (sort === "title_asc") {
      finalData.sort((a, b) => a.title.localeCompare(b.title));
    } else if (sort === "title_desc") {
      finalData.sort((a, b) => b.title.localeCompare(a.title));
    }

    return finalData;
  };

  const fetchTVShows = () => {
    setLoading(true);

    let url = "";

    if (searchTerm.trim()) {
      url = `${API_URL}/tv-shows/?search=${encodeURIComponent(
        searchTerm.trim()
      )}&sort=${sort}`;
    } else if (selectedGenre === "Recommended") {
      url = `${API_URL}/tv-shows/?sort=rating&limit=30`;
    } else {
      url = `${API_URL}/tv-shows/?sort=${sort}&genre=${encodeURIComponent(
        selectedGenre
      )}`;
    }

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        const finalData =
          selectedGenre === "Recommended" && !searchTerm.trim()
            ? sortRecommendedShows(data)
            : data;

        setTvShows(finalData);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching TV shows:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    sessionStorage.setItem("tvShowsGenre", selectedGenre);
  }, [selectedGenre]);

  useEffect(() => {
    sessionStorage.setItem("tvShowsSort", sort);
  }, [sort]);

  useEffect(() => {
    fetchTVShows();
  }, [selectedGenre, sort, searchTerm]);

  return (
    <div className="page">
      <div className="movies-header">
        <h1 className="page-title">
          {searchTerm.trim()
            ? `Search results for "${searchTerm}"`
            : selectedGenre === "Recommended"
            ? "Recommended TV Shows"
            : selectedGenre}
        </h1>

        <select
          className="sort-select"
          value={sort}
          onChange={(e) => setSort(e.target.value)}
        >
          <option value="rating">Highest Rated</option>
          <option value="year_desc">Newest</option>
          <option value="year_asc">Oldest</option>
          <option value="title_asc">A-Z</option>
          <option value="title_desc">Z-A</option>
        </select>
      </div>

      {!searchTerm.trim() && (
        <div className="genre-tabs-wrapper">
          <button className="genre-arrow left" onClick={() => scrollGenres("left")}>
            ‹
          </button>

          <div className="genre-tabs" ref={tabsRef}>
            {genres.map((genre) => (
              <button
                key={genre}
                className={`genre-tab ${
                  selectedGenre === genre ? "active" : ""
                }`}
                onClick={() => setSelectedGenre(genre)}
              >
                {genre}
              </button>
            ))}
          </div>

          <button className="genre-arrow right" onClick={() => scrollGenres("right")}>
            ›
          </button>
        </div>
      )}

      {loading && <p className="empty-message">Loading TV shows...</p>}

      {!loading && tvShows.length === 0 && (
        <p className="empty-message">No TV shows found.</p>
      )}

      {!loading && (
        <div className="movies-grid">
          {tvShows.map((tvShow) => (
            <TVShowCard key={tvShow.id} tvShow={tvShow} />
          ))}
        </div>
      )}
    </div>
  );
}

export default TVShows;