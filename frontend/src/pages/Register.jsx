import { useState } from "react";
import { Link, useNavigate, Navigate, useLocation } from "react-router-dom";

function Register() {
  const navigate = useNavigate();
  const location = useLocation();

  if (!location.state?.fromLogin) {
    return <Navigate to="/" />;
  }

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const passwordsMatch = password === confirmPassword;

  async function handleSubmit(e) {
    e.preventDefault();

    if (!passwordsMatch) {
      setError("Passwords do not match");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          email,
          password,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Registration failed");
      }

      navigate("/"); // nazad na login
    } catch (err) {
      setError(err.message);
    }
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
          <h2>Start building your movie collection.</h2>
        </div>
      </div>

      <div className="auth-panel">
        <form className="auth-box" onSubmit={handleSubmit}>
          <h2>Create account</h2>

          <p className="auth-subtitle">
            Start building your movie collection.
          </p>

          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
            />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email"
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
            />
          </div>

          <div className="form-group">
            <label>Confirm password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repeat password"
            />
          </div>

          {error && <p className="error-text">{error}</p>}

          <button
            className="auth-button"
            disabled={!passwordsMatch || !username}
          >
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