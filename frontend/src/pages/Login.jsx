import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../context/AuthContext";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { setUser } = useAuth();

  async function handleSubmit(e) {
    e.preventDefault();

    try {
      const response = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (!response.ok) {
        throw new Error("Invalid credentials");
      }

     const data = await response.json();

    localStorage.setItem("token", data.access_token);
    localStorage.setItem("token_type", data.token_type);

      const me = await fetch("http://127.0.0.1:8000/auth/me", {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });

      const userData = await me.json();

      setUser(userData);
      navigate("/home");
    } catch (err) {
      setError("Wrong email or password");
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
          <h1>Movie Tracker</h1>
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

          <button className="auth-button">Login</button>

          {error && <p className="error-text">{error}</p>}

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