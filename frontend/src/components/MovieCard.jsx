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
  const handleActionClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <Link to={`/movies/${movie.id}`} className="movie-card-link">
      <div className="movie-card">
        <div className="poster-wrapper">
          <img
            src={movie.poster}
            alt={movie.title}
            className="movie-poster"
          />

          {isWatched && <span className="status-badge">Watched</span>}
        </div>

        <div className="movie-info">
          <h3 className="movie-title">{movie.title}</h3>

          <p className="movie-meta">
            {movie.year} • ⭐ {movie.imdb_rating}
          </p>
        </div>

        <div className="card-actions" onClick={handleActionClick}>
          {showRemove ? (
            <>
              <button onClick={() => onRemove(movie.id)}>Remove</button>
              <button onClick={() => onMarkWatched(movie)}>Watched</button>
            </>
          ) : (
            <>

            </>
          )}
        </div>
      </div>
    </Link>
  );
}

export default MovieCard;