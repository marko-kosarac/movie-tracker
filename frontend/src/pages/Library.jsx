import MovieCard from "../components/MovieCard";

function Library({ watchlist, removeFromWatchlist }) {
  return (
    <div>
      <h1>Library</h1>

      {watchlist.length === 0 ? (
        <p>No movies in watchlist.</p>
      ) : (
        watchlist.map((movie) => (
          <MovieCard
            key={movie.id}
            movie={movie}
            showRemove={true}
            onRemove={removeFromWatchlist}
          />
        ))
      )}
    </div>
  );
}

export default Library;