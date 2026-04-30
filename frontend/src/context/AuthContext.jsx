import { createContext, useContext, useEffect, useState } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    fetch("http://127.0.0.1:8000/auth/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error("Invalid token");
        }

        return res.json();
      })
      .then((data) => {
        setUser(data);
      })
      .catch(() => {
        localStorage.removeItem("token");
        localStorage.removeItem("token_type");
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("token_type");

    sessionStorage.removeItem("moviesGenre");
    sessionStorage.removeItem("moviesSort");
    sessionStorage.removeItem("moviesScroll");
    sessionStorage.removeItem("moviesSearch");

    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}