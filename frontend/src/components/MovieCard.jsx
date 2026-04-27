import { Link } from "react-router-dom";

function MovieCard({
  movie,
  isInWatchlist,
  isWatched,
  onAdd,
  onRemove,
  onMarkWatched,
  showRemove = false,
}) {
  return (
    <Link to={`/movies/${movie.id}`} className="movie-card-link">
      <div className="movie-card">
        <img src={movie.poster} alt={movie.title} className="movie-poster" />

        {isWatched && <span className="status-badge">Watched</span>}

        <div className="movie-overlay">
          <h3 className="movie-title">{movie.title}</h3>
          <p className="movie-meta">
            {movie.year} • ⭐ {movie.rating}
          </p>
        </div>

        <div className="card-actions" onClick={(e) => e.preventDefault()}>
          {showRemove ? (
            <>
              <button onClick={() => onRemove(movie.id)}>Remove</button>
              <button onClick={() => onMarkWatched(movie)}>Watched</button>
            </>
          ) : (
            <>
              <button
                onClick={() => onAdd(movie)}
                disabled={isInWatchlist || isWatched}
              >
                {isInWatchlist ? "Added" : isWatched ? "Watched" : "Add"}
              </button>

              <button onClick={() => onMarkWatched(movie)} disabled={isWatched}>
                {isWatched ? "Watched" : "Mark"}
              </button>
            </>
          )}
        </div>
      </div>
    </Link>
  );
}

export default MovieCard;