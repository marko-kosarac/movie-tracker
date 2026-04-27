import { useState } from "react";
import { movies } from "../movies";
import MovieCard from "../components/MovieCard";

function Movies({ watchlist, watched, addToWatchlist, markAsWatched }) {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredMovies = movies.filter((movie) =>
    movie.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

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