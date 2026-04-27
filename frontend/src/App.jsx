import { useState } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import Movies from "./pages/Movies";
import MovieDetails from "./pages/MovieDetails";
import Library from "./pages/Library";

function AppContent() {
  const [watchlist, setWatchlist] = useState([]);
  const [watched, setWatched] = useState([]);

  const location = useLocation();
  const isAuthPage = location.pathname === "/" || location.pathname === "/register";

  function addToWatchlist(movie) {
    const exists = watchlist.some((item) => item.id === movie.id);
    if (exists) return;

    setWatchlist([...watchlist, movie]);
  }

  function removeFromWatchlist(movieId) {
    setWatchlist(watchlist.filter((movie) => movie.id !== movieId));
  }

  function markAsWatched(movie) {
    const alreadyWatched = watched.some((item) => item.id === movie.id);

    if (!alreadyWatched) {
      setWatched([...watched, movie]);
    }

    setWatchlist(watchlist.filter((item) => item.id !== movie.id));
  }

  return (
    <div className="app">
      {!isAuthPage && (
        <nav className="navbar">
          <Link to="/home">Home</Link>
          <Link to="/movies">Movies</Link>
          <Link to="/library">Library</Link>
        </nav>
      )}

      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route path="/home" element={<Home />} />

        <Route
          path="/movies"
          element={
            <Movies
              watchlist={watchlist}
              watched={watched}
              addToWatchlist={addToWatchlist}
              markAsWatched={markAsWatched}
            />
          }
        />

        <Route
          path="/movies/:id"
          element={
            <MovieDetails
              watchlist={watchlist}
              watched={watched}
              addToWatchlist={addToWatchlist}
              markAsWatched={markAsWatched}
            />
          }
        />

        <Route
          path="/library"
          element={
            <Library
              watchlist={watchlist}
              watched={watched}
              removeFromWatchlist={removeFromWatchlist}
              markAsWatched={markAsWatched}
            />
          }
        />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;