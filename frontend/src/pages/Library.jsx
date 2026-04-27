import MovieCard from "../components/MovieCard";

function Library({ watchlist, watched, removeFromWatchlist, markAsWatched }) {
  return (
    <div className="page">
      <h1 className="page-title">Library</h1>

      <h2>Watchlist</h2>

      {watchlist.length === 0 ? (
        <p className="empty-message">No movies in watchlist.</p>
      ) : (
        <div className="movies-grid">
          {watchlist.map((movie) => (
            <MovieCard
              key={movie.id}
              movie={movie}
              showRemove={true}
              onRemove={removeFromWatchlist}
              onMarkWatched={markAsWatched}
            />
          ))}
        </div>
      )}

      <h2 className="section-title">Watched</h2>

      {watched.length === 0 ? (
        <p className="empty-message">No watched movies yet.</p>
      ) : (
        <div className="movies-grid">
          {watched.map((movie) => (
            <MovieCard
              key={movie.id}
              movie={movie}
              isWatched={true}
              onAdd={() => {}}
              onMarkWatched={() => {}}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default Library;