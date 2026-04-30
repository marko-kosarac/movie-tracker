import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import MovieCard from "../components/MovieCard";

function Movies({ watchlist, watched, addToWatchlist, markAsWatched }) {
  const [movies, setMovies] = useState([]);

  const [selectedGenre, setSelectedGenre] = useState(
    sessionStorage.getItem("moviesGenre") || "Recommended"
  );

  const [sort, setSort] = useState(
    sessionStorage.getItem("moviesSort") || "rating"
  );

  const [loading, setLoading] = useState(true);

  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const searchTerm = queryParams.get("search") || "";

  const tabsRef = useRef(null);

  const genres = [
    "Recommended",
    "Action",
    "Drama",
    "Comedy",
    "Adventure",
    "Crime",
    "Romance",
    "Thriller",
    "Horror",
    "Fantasy",
    "Animation",
    "Family",
    "Science Fiction",
  ];

  const scrollGenres = (direction) => {
    if (tabsRef.current) {
      tabsRef.current.scrollBy({
        left: direction === "left" ? -300 : 300,
        behavior: "smooth",
      });
    }
  };

  const sortRecommendedMovies = (data) => {
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

  const fetchMovies = () => {
    setLoading(true);

    let url = "";

    if (searchTerm.trim()) {
      url = `http://127.0.0.1:8000/movies/?search=${encodeURIComponent(
        searchTerm.trim()
      )}&sort=${sort}`;
    } else if (selectedGenre === "Recommended") {
      url = "http://127.0.0.1:8000/movies/?sort=rating&limit=30";
    } else {
      url = `http://127.0.0.1:8000/movies/?sort=${sort}&genre=${encodeURIComponent(
        selectedGenre
      )}`;
    }

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        const finalData =
          selectedGenre === "Recommended" && !searchTerm.trim()
            ? sortRecommendedMovies(data)
            : data;

        setMovies(finalData);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    sessionStorage.setItem("moviesGenre", selectedGenre);
  }, [selectedGenre]);

  useEffect(() => {
    sessionStorage.setItem("moviesSort", sort);
  }, [sort]);

  useEffect(() => {
    const handleScroll = () => {
      sessionStorage.setItem("moviesScroll", window.scrollY.toString());
    };

    window.addEventListener("scroll", handleScroll);

    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  useEffect(() => {
    fetchMovies();
  }, [selectedGenre, sort, searchTerm]);

  useEffect(() => {
    if (!loading) {
      const savedScroll = sessionStorage.getItem("moviesScroll");

      if (savedScroll) {
        setTimeout(() => {
          window.scrollTo(0, Number(savedScroll));
        }, 100);
      }
    }
  }, [loading]);

  return (
    <div className="page">
      <div className="movies-header">
        <h1 className="page-title">
          {searchTerm.trim()
            ? `Search results for "${searchTerm}"`
            : selectedGenre === "Recommended"
            ? "Recommended"
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
          <button
            className="genre-arrow left"
            onClick={() => scrollGenres("left")}
          >
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

          <button
            className="genre-arrow right"
            onClick={() => scrollGenres("right")}
          >
            ›
          </button>
        </div>
      )}

      {loading && <p className="empty-message">Loading movies...</p>}

      {!loading && movies.length === 0 && (
        <p className="empty-message">No movies found.</p>
      )}

      {!loading && (
        <div className="movies-grid">
          {movies.map((movie) => {
            const isInWatchlist = watchlist.some((m) => m.id === movie.id);
            const isWatched = watched.some((m) => m.id === movie.id);

            return (
              <MovieCard
                key={movie.id}
                movie={movie}
                isInWatchlist={isInWatchlist}
                isWatched={isWatched}
                onAdd={addToWatchlist}
                onMarkWatched={markAsWatched}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Movies;