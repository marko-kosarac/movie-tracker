import { movies } from "../movies";
import MovieCard from "../components/MovieCard";

function Movies({ watchlist, addToWatchlist }) {
  return (
    <div>
      <h1>Movies</h1>

      {movies.map((movie) => {
        const isInWatchlist = watchlist.some((item) => item.id === movie.id);

        return (
          <MovieCard
            key={movie.id}
            movie={movie}
            isInWatchlist={isInWatchlist}
            onAdd={addToWatchlist}
          />
        );
      })}
    </div>
  );
}

export default Movies;