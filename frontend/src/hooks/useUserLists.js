import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";

const API = "http://127.0.0.1:8000";

function authHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export function useUserLists() {
  const [watchlist, setWatchlist] = useState([]);
  const [watched, setWatched] = useState([]);
  const { user } = useAuth();

  useEffect(() => {
    if (!user) {
      setWatchlist([]);
      setWatched([]);
      return;
    }

    fetch(`${API}/lists/`, { headers: authHeaders() })
      .then((r) => r.json())
      .then((data) => {
        setWatchlist(data.watchlist || []);
        setWatched(data.watched || []);
      })
      .catch(console.error);
  }, [user]);

  const addToWatchlist = useCallback(async (item) => {
    const itemType = item.type || "movie";
    if (watchlist.some((i) => i.id === item.id && i.type === itemType)) return;

    setWatchlist((prev) => [...prev, { ...item, type: itemType }]);

    try {
      const res = await fetch(`${API}/lists/watchlist`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ item_id: item.id, item_type: itemType }),
      });
      if (!res.ok) {
        setWatchlist((prev) =>
          prev.filter((i) => !(i.id === item.id && i.type === itemType))
        );
      }
    } catch {
      setWatchlist((prev) =>
        prev.filter((i) => !(i.id === item.id && i.type === itemType))
      );
    }
  }, [watchlist]);

  const markAsWatched = useCallback(async (item) => {
    const itemType = item.type || "movie";

    setWatchlist((prev) =>
      prev.filter((i) => !(i.id === item.id && i.type === itemType))
    );
    setWatched((prev) => {
      if (prev.some((i) => i.id === item.id && i.type === itemType)) return prev;
      return [...prev, { ...item, type: itemType }];
    });

    try {
      await fetch(`${API}/lists/watched`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ item_id: item.id, item_type: itemType }),
      });
    } catch (err) {
      console.error(err);
    }
  }, []);

  const removeFromWatchlist = useCallback(async (item) => {
    const itemType = item.type || "movie";
    setWatchlist((prev) =>
      prev.filter((i) => !(i.id === item.id && i.type === itemType))
    );

    try {
      await fetch(`${API}/lists/watchlist/${itemType}/${item.id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
    } catch (err) {
      console.error(err);
    }
  }, []);

  const removeFromWatched = useCallback(async (item) => {
    const itemType = item.type || "movie";
    setWatched((prev) =>
      prev.filter((i) => !(i.id === item.id && i.type === itemType))
    );

    try {
      await fetch(`${API}/lists/watched/${itemType}/${item.id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
    } catch (err) {
      console.error(err);
    }
  }, []);

  const refreshLists = useCallback(() => {
    fetch(`${API}/lists/`, { headers: authHeaders() })
      .then((r) => r.json())
      .then((data) => {
        setWatchlist(data.watchlist || []);
        setWatched(data.watched || []);
      })
      .catch(console.error);
  }, []);

  return {
    watchlist,
    watched,
    addToWatchlist,
    markAsWatched,
    removeFromWatchlist,
    removeFromWatched,
    refreshLists,
  };
}
