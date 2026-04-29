import { useState } from "react";
import { useAuth } from "./context/AuthContext";
import Profile from "./pages/Profile";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useLocation,
  Navigate,
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import Movies from "./pages/Movies";
import MovieDetails from "./pages/MovieDetails";
import Library from "./pages/Library";
import avatar0 from "./assets/avatars/default.png";
import avatar1 from "./assets/avatars/boy.png";
import avatar2 from "./assets/avatars/boy2.png";
import avatar3 from "./assets/avatars/boy3.png";
import avatar4 from "./assets/avatars/boy4.png";
import avatar5 from "./assets/avatars/boy5.png";
import avatar6 from "./assets/avatars/girl.png";
import avatar7 from "./assets/avatars/girl2.png";
import avatar8 from "./assets/avatars/girl3.png";
import avatar9 from "./assets/avatars/girl4.png";
import avatar10 from "./assets/avatars/girl5.png";

const avatarMap = {
  avatar0,
  avatar1,
  avatar2,
  avatar3,
  avatar4,
  avatar5,
  avatar6,
  avatar7,
  avatar8,
  avatar9,
  avatar10,
};

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("token");

  if (!token) {
    return <Navigate to="/" />;
  }

  return children;
}

function AppContent() {
  const [watchlist, setWatchlist] = useState([]);
  const [watched, setWatched] = useState([]);

  const location = useLocation();
  const isAuthPage = location.pathname === "/" || location.pathname === "/register";
  const { user } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

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

  function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("token_type");
    window.location.href = "/";
  }

  return (
    <div className="app">
      {!isAuthPage && (
        <nav className="navbar">
  <div className="nav-links">
    <Link to="/home">Home</Link>
    <Link to="/movies">Movies</Link>
    <Link to="/library">Library</Link>
  </div>

<div className="user-menu">
  <button
    className="user-menu-button"
    onClick={() => setMenuOpen(!menuOpen)}
  >
    <img
      src={avatarMap[user?.avatar] || avatarMap.avatar0}
      alt="avatar"
      className="navbar-avatar"
    />
  </button>

  {menuOpen && (
    <div className="dropdown-menu user-dropdown">
      <Link
        to="/profile"
        className="dropdown-profile"
        onClick={() => setMenuOpen(false)}
      >
        <img
          src={avatarMap[user?.avatar] || avatarMap.avatar0}
          alt="avatar"
          className="dropdown-avatar"
        />

        <span>{user?.username}</span>
      </Link>

      <div className="dropdown-separator"></div>

      <button onClick={handleLogout}>Logout</button>
    </div>
  )}
</div>
</nav>
      )}

      <Routes>
        <Route path="/" element={<Login />} />

        <Route path="/register" element={<Register />} />

        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />

        <Route
          path="/movies"
          element={
            <ProtectedRoute>
              <Movies
                watchlist={watchlist}
                watched={watched}
                addToWatchlist={addToWatchlist}
                markAsWatched={markAsWatched}
              />
            </ProtectedRoute>
          }
        />

        <Route
          path="/movies/:id"
          element={
            <ProtectedRoute>
              <MovieDetails
                watchlist={watchlist}
                watched={watched}
                addToWatchlist={addToWatchlist}
                markAsWatched={markAsWatched}
              />
            </ProtectedRoute>
          }
        />

        <Route
          path="/library"
          element={
            <ProtectedRoute>
              <Library
                watchlist={watchlist}
                watched={watched}
                removeFromWatchlist={removeFromWatchlist}
                markAsWatched={markAsWatched}
              />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
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