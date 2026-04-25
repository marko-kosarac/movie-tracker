import { useState } from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

import Home from "./pages/Home";
import Movies from "./pages/Movies";
import MovieDetails from "./pages/MovieDetails";
import Library from "./pages/Library";

function App() {
  const [watchlist, setWatchlist] = useState([]);

  function addToWatchlist(movie) {
    const exists = watchlist.some((item) => item.id === movie.id);
    if (exists) return;

    setWatchlist([...watchlist, movie]);
  }

  function removeFromWatchlist(movieId) {
    setWatchlist(watchlist.filter((m) => m.id !== movieId));
  }

  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Home</Link> |{" "}
        <Link to="/movies">Movies</Link> |{" "}
        <Link to="/library">Library</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />

        <Route
          path="/movies"
          element={
            <Movies
              watchlist={watchlist}
              addToWatchlist={addToWatchlist}
            />
          }
        />

        <Route
          path="/movies/:id"
          element={
            <MovieDetails
              watchlist={watchlist}
              addToWatchlist={addToWatchlist}
            />
          }
        />

        <Route
          path="/library"
          element={
            <Library
              watchlist={watchlist}
              removeFromWatchlist={removeFromWatchlist}
            />
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;