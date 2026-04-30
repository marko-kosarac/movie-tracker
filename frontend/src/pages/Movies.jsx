import { useEffect, useState } from "react";
import MovieCard from "../components/MovieCard";

function Movies({ watchlist, watched, addToWatchlist, markAsWatched }) {
  const [movies, setMovies] = useState([]);
  const [searchTerm, setSearchTerm] = useState(
    sessionStorage.getItem("moviesSearch") || ""
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/movies/")
      .then((res) => res.json())
      .then((data) => {
        setMovies(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching movies:", error);
        setLoading(false);
      });
  }, []);

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
    sessionStorage.setItem("moviesSearch", searchTerm);
  }, [searchTerm]);

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

  const filteredMovies = movies.filter((movie) =>
    movie.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="page">
        <h1 className="page-title">Loading movies...</h1>
      </div>
    );
  }

  return (
    <div className="page">
      <h1 className="page-title">Movies</h1>

      <input
        className="search-input"
        type="text"
        placeholder="Search movies..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      <div className="movies-grid">
        {filteredMovies.map((movie) => {
          const isInWatchlist = watchlist.some((item) => item.id === movie.id);
          const isWatched = watched.some((item) => item.id === movie.id);

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
    </div>
  );
}

export default Movies;