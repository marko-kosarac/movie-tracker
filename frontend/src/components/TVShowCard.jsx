import { Link } from "react-router-dom";
import "./MovieCard.css";

function TVShowCard({
  tvShow,
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
    <Link to={`/tv-shows/${tvShow.id}`} className="movie-card-link">
      <div className="movie-card">
        <div className="poster-wrapper">
          <img
            src={tvShow.poster}
            alt={tvShow.title}
            className="movie-poster"
          />

          {isWatched && <span className="status-badge">Watched</span>}
        </div>

        <div className="movie-info">
          <h3 className="movie-title">
            {tvShow.title}
          </h3>

          <p className="tv-show-seasons">
            {tvShow.seasons_count}{" "}
            {tvShow.seasons_count === 1 ? "Season" : "Seasons"}
          </p>

          <p className="movie-meta">
            {tvShow.year} • ⭐ {tvShow.imdb_rating}
          </p>
        </div>

        {showRemove && (
          <div className="card-actions" onClick={handleActionClick}>
            {!isWatched && (
              <button
                className="card-btn card-btn--watched"
                onClick={() => onMarkWatched(tvShow)}
              >
                ✓ Watched
              </button>
            )}
            <button
              className="card-btn card-btn--remove"
              onClick={() => onRemove(tvShow)}
            >
              ✕ Remove
            </button>
          </div>
        )}
      </div>
    </Link>
  );
}

export default TVShowCard;