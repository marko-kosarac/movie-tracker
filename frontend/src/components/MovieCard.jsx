import { Link } from "react-router-dom";

function MovieCard({ movie, isInWatchlist, onAdd, onRemove, showRemove = false }) {
  return (
    <div>
      <h3>
        {movie.title} ({movie.year})
      </h3>

      <Link to={`/movies/${movie.id}`}>View Details</Link>

      <div>
        {showRemove ? (
          <button onClick={() => onRemove(movie.id)}>Remove</button>
        ) : (
          <button onClick={() => onAdd(movie)} disabled={isInWatchlist}>
            {isInWatchlist ? "Added" : "Add to Watchlist"}
          </button>
        )}
      </div>
    </div>
  );
}

export default MovieCard;