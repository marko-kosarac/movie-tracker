import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

function MovieDetails({ watchlist, watched, addToWatchlist, markAsWatched }) {
  const { id } = useParams();
  const [movie, setMovie] = useState(null);

  useEffect(() => {
    fetch(`http://127.0.0.1:8000/movies/${id}`)
      .then((res) => res.json())
      .then((data) => setMovie(data))
      .catch((err) => console.error(err));
  }, [id]);

  if (!movie) return <h1 className="page">Loading...</h1>;

  const isInWatchlist = watchlist.some((item) => item.id === movie.id);
  const isWatched = watched.some((item) => item.id === movie.id);

  return (
    <div
      className="movie-details-hero"
      style={{
        backgroundImage: `url(${movie.backdrop || movie.poster})`
      }}
    >
      <div className="movie-details-gradient">
        <div className="movie-details-content">
          <h1>{movie.title}</h1>

          <p className="movie-details-meta">
            {movie.year} • IMDb ⭐ {movie.imdb_rating} • {movie.genre}
          </p>

          <div className="movie-details-actions">
            <button
              className={`action-btn ${isInWatchlist ? "active" : ""}`}
              onClick={() => addToWatchlist(movie)}
            >
              {isInWatchlist ? "✓ My List" : "+ My List"}
            </button>

            <button
              className={`action-btn ${isWatched ? "active" : ""}`}
              onClick={() => markAsWatched(movie)}
            >
              {isWatched ? "✓ Watched" : "👁 Mark as Watched"}
            </button>
          </div>

          <div className="movie-details-section">
            <h3>Actors</h3>
            <p>{movie.actors}</p>
          </div>

          <div className="movie-details-section">
            <h3>Description</h3>
            <p>{movie.description}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MovieDetails;