import { useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";

function Register() {
  const location = useLocation();

  if (!location.state?.fromLogin) {
    return <Navigate to="/" />;
  }

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const passwordsMatch = password === confirmPassword;

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
          <h2>Start building your personal movie collection.</h2>
        </div>
      </div>

      <div className="auth-panel">
        <form className="auth-box">
          <h2>Create account</h2>

          <p className="auth-subtitle">
            Start building your movie collection.
          </p>

          <div className="form-group">
            <label>Username</label>
            <input type="text" placeholder="Enter username" />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input type="email" placeholder="Enter email" />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Confirm password</label>
            <input
              type="password"
              placeholder="Repeat password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />

            {!passwordsMatch && confirmPassword && (
              <p className="error-text">Passwords do not match</p>
            )}
          </div>

          <button className="auth-button" disabled={!passwordsMatch}>
            Register
          </button>

          <p className="auth-switch">
            Already have an account? <Link to="/">Login</Link>
          </p>
        </form>
      </div>
    </div>
  );
}

export default Register;