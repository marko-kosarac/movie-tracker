import { useState } from "react";
import { useAuth } from "./context/AuthContext";
import Profile from "./pages/Profile";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useLocation,
  useNavigate,
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
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="page">Loading...</div>;
  }

  if (!token || !user) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function AppContent() {
  const [watchlist, setWatchlist] = useState([]);
  const [watched, setWatched] = useState([]);
  const [menuOpen, setMenuOpen] = useState(false);

  const [showSearch, setShowSearch] = useState(false);
  const [searchValue, setSearchValue] = useState("");

  const location = useLocation();
  const isMoviesPage = location.pathname === "/movies";
  const navigate = useNavigate();
  const isAuthPage = location.pathname === "/" || location.pathname === "/register";
  const { user } = useAuth();

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

  sessionStorage.removeItem("moviesGenre");
  sessionStorage.removeItem("moviesSort");
  sessionStorage.removeItem("moviesScroll");
  sessionStorage.removeItem("moviesSearch");

  setMenuOpen(false);

  navigate("/", { replace: true });
}

  function handleSearch(e) {
    if (e.key === "Enter" && searchValue.trim()) {
      navigate(`/movies?search=${encodeURIComponent(searchValue.trim())}`);
      setShowSearch(false);
    }

    if (e.key === "Escape") {
      setShowSearch(false);
      setSearchValue("");
    }
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

<div className="nav-right">
  {isMoviesPage && (
  <div className="search-wrapper">
    {!showSearch && (
      <button
        className="search-icon"
        onClick={() => setShowSearch(true)}
      >
        🔍
      </button>
    )}

    {showSearch && (
      <input
        className="nav-search-input"
        autoFocus
        type="text"
        placeholder="Search movies..."
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
        onKeyDown={handleSearch}
        onBlur={() => setShowSearch(false)}
      />
    )}
  </div>)}

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