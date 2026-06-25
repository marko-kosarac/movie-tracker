import { useRef } from "react";
import MovieCard from "../components/MovieCard";
import "./Library.css";

function HorizontalRow({ items, onRemove, onMarkWatched, isWatched = false }) {
  const rowRef = useRef(null);

  const scroll = (direction) => {
    if (rowRef.current) {
      rowRef.current.scrollBy({ left: direction === "left" ? -520 : 520, behavior: "smooth" });
    }
  };

  return (
    <div className="library-row-wrapper">
      <button className="library-arrow" onClick={() => scroll("left")}>‹</button>
      <div className="library-row" ref={rowRef}>
        {items.map((item) => (
          <MovieCard
            key={`${item.type}_${item.id}`}
            movie={item}
            isWatched={isWatched}
            showRemove={true}
            onRemove={onRemove}
            onMarkWatched={onMarkWatched}
          />
        ))}
      </div>
      <button className="library-arrow" onClick={() => scroll("right")}>›</button>
    </div>
  );
}

function Library({ watchlist, watched, removeFromWatchlist, removeFromWatched, markAsWatched }) {
  return (
    <div className="page">
      <h1 className="page-title">Library</h1>

      <h2>Watchlist</h2>

      {watchlist.length === 0 ? (
        <p className="empty-message">No items in watchlist.</p>
      ) : (
        <HorizontalRow
          items={watchlist}
          onRemove={removeFromWatchlist}
          onMarkWatched={markAsWatched}
        />
      )}

      <h2 className="section-title">Watched</h2>

      {watched.length === 0 ? (
        <p className="empty-message">No watched items yet.</p>
      ) : (
        <HorizontalRow
          items={watched}
          isWatched={true}
          onRemove={removeFromWatched}
          onMarkWatched={() => {}}
        />
      )}
    </div>
  );
}

export default Library;
