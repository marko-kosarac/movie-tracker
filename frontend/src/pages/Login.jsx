import { Link, useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();

  function handleSubmit(e) {
    e.preventDefault();

    // kasnije ide prava backend provjera
    navigate("/home");
  }

  return (
    <div className="auth-page">
      <div
        className="auth-image"
        style={{
          backgroundImage:
            "url(https://cdn.wallpapersafari.com/38/57/YEX1h4.jpg)",
        }}
      >
        <div className="auth-image-overlay">
          <h1>CineTrack</h1>
          <h2>Your personal movie library.</h2>
        </div>
      </div>

      <div className="auth-panel">
        <form className="auth-box" onSubmit={handleSubmit}>
          <h2>Welcome back</h2>

          <p className="auth-subtitle">
            Log in to continue tracking your movies.
          </p>

          <div className="form-group">
            <label>Email</label>
            <input type="email" placeholder="Enter email" />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input type="password" placeholder="Enter password" />
          </div>

          <button className="auth-button">Login</button>

          <p className="auth-switch">
            Don&apos;t have an account?{" "}
            <Link to="/register" state={{ fromLogin: true }}>
              Register
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default Login;