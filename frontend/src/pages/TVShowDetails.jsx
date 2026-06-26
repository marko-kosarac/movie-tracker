import { useParams } from "react-router-dom";
import { useEffect, useState, useRef } from "react";
import { API_URL } from "../config";
import "./MovieDetails.css";
import "./TVShowDetails.css";

function TVShowDetails({ watchlist, watched, addToWatchlist, markAsWatched }) {
  const { id } = useParams();
  const [tvShow, setTvShow] = useState(null);
  const [selectedSeasonId, setSelectedSeasonId] = useState("");
  const episodesListRef = useRef(null);

  useEffect(() => {
    fetch(`${API_URL}/tv-shows/${id}`)
      .then((res) => res.json())
      .then((data) => {
        setTvShow(data);

        if (data.seasons && data.seasons.length > 0) {
          setSelectedSeasonId(String(data.seasons[0].id));
        }
      })
      .catch((err) => console.error(err));
  }, [id]);

  if (!tvShow) return <h1 className="page">Loading...</h1>;

  const isInWatchlist = watchlist.some((item) => item.id === tvShow.id);
  const isWatched = watched.some((item) => item.id === tvShow.id);

  const selectedSeason = tvShow.seasons?.find(
    (season) => String(season.id) === selectedSeasonId
  );

  const seasonsCount = tvShow.seasons?.length || 0;

  return (
    <div
      className="movie-details-hero"
      style={{
        backgroundImage: `url(${tvShow.backdrop || tvShow.poster})`,
      }}
    >
      <div className="movie-details-gradient">
        <div className="movie-details-content tv-show-details-content">
          <h1>{tvShow.title}</h1>

          <p className="movie-details-meta">
            {tvShow.year} • IMDb ⭐ {tvShow.imdb_rating} • {seasonsCount}{" "}
            {seasonsCount === 1 ? "Season" : "Seasons"} • {tvShow.genre}
          </p>

                    <div className="movie-details-actions">
            <button
              className={`action-btn ${isInWatchlist ? "active" : ""}`}
              onClick={() => addToWatchlist(tvShow)}
            >
              {isInWatchlist ? "✓ My List" : "+ My List"}
            </button>

            <button
              className={`action-btn ${isWatched ? "active" : ""}`}
              onClick={() => markAsWatched(tvShow)}
            >
              {isWatched ? "✓ Watched" : "👁 Mark as Watched"}
            </button>
          </div>

          <div className="movie-details-section">
            <h3>Actors</h3>
            <p>{tvShow.actors}</p>
          </div>

          <div className="movie-details-section">
            <h3>Description</h3>
            <p>{tvShow.description}</p>
          </div>

          <div className="episodes-section">
            <div className="episodes-header">
              <h2>Episodes</h2>

              {tvShow.seasons && tvShow.seasons.length > 0 && (
                <select
                  className="season-select"
                  value={selectedSeasonId}
                  onChange={(e) => setSelectedSeasonId(e.target.value)}
                >
                  {tvShow.seasons
                    .sort((a, b) => a.season_number - b.season_number)
                    .map((season) => (
                      <option key={season.id} value={season.id}>
                        Season {season.season_number}
                      </option>
                    ))}
                </select>
              )}
            </div>

            {!selectedSeason || selectedSeason.episodes.length === 0 ? (
              <p className="empty-message">No episodes found.</p>
            ) : (
            <div className="episodes-wrapper">
            <button
                className="episodes-arrow up"
                onClick={() => {
                  episodesListRef.current?.scrollBy({ top: -200, behavior: "smooth" });
                }}
            >
                ▲
            </button>

            <div className="episodes-list" ref={episodesListRef}>
                {selectedSeason.episodes
                .sort((a, b) => a.episode_number - b.episode_number)
                .map((episode) => (
                    <div className="episode-card" key={episode.id}>
                    <div className="episode-number">
                        E{episode.episode_number}
                    </div>

                    <div className="episode-info">
                        <h3>{episode.title}</h3>
                        <p>{episode.description || "No description available."}</p>
                    </div>
                    </div>
                ))}
            </div>

            <button
                className="episodes-arrow down"
                onClick={() => {
                  episodesListRef.current?.scrollBy({ top: 200, behavior: "smooth" });
                }}
            >
                ▼
            </button>
            </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TVShowDetails;