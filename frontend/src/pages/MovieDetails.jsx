import { useParams } from "react-router-dom";
import { movies } from "../movies";

function MovieDetails({ watchlist, addToWatchlist }) {
  const { id } = useParams();

  const movie = movies.find((m) => m.id === Number(id));

  if (!movie) return <h1>Movie not found</h1>;

  const isInWatchlist = watchlist.some((item) => item.id === movie.id);

  return (
    <div>
      <h1>{movie.title}</h1>
      <p>Year: {movie.year}</p>

      <button onClick={() => addToWatchlist(movie)} disabled={isInWatchlist}>
        {isInWatchlist ? "Added" : "Add to Watchlist"}
      </button>
    </div>
  );
}

export default MovieDetails;