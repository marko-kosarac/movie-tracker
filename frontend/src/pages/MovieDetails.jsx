import { useParams } from "react-router-dom";
import { movies } from "../movies";

function MovieDetails({ watchlist, watched, addToWatchlist, markAsWatched }) {
  const { id } = useParams();

  const movie = movies.find((m) => m.id === Number(id));

  if (!movie) return <h1>Movie not found</h1>;

  const isInWatchlist = watchlist.some((item) => item.id === movie.id);
  const isWatched = watched.some((item) => item.id === movie.id);

return (
  <div className="page">
    <div className="details-card">
      <h1 className="page-title">{movie.title}</h1>
      <p className="movie-year">Year: {movie.year}</p>

      <div className="card-actions">
        <button onClick={() => addToWatchlist(movie)} disabled={isInWatchlist || isWatched}>
          {isInWatchlist ? "Added" : isWatched ? "Watched" : "Add to Watchlist"}
        </button>

        <button onClick={() => markAsWatched(movie)} disabled={isWatched}>
          {isWatched ? "Watched" : "Mark as Watched"}
        </button>
      </div>
    </div>
  </div>
);
}

export default MovieDetails;