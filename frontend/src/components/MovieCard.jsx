import { Link } from "react-router-dom";
import "./MovieCard.css";

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

  const linkTo = movie.type === "tv_show" ? `/tv-shows/${movie.id}` : `/movies/${movie.id}`;

  return (
    <Link to={linkTo} className="movie-card-link">
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

        {showRemove && (
          <div className="card-actions" onClick={handleActionClick}>
            {!isWatched && (
              <button
                className="card-btn card-btn--watched"
                onClick={() => onMarkWatched(movie)}
              >
                ✓ Watched
              </button>
            )}
            <button
              className="card-btn card-btn--remove"
              onClick={() => onRemove(movie)}
            >
              ✕ Remove
            </button>
          </div>
        )}
      </div>
    </Link>
  );
}

export default MovieCard;
