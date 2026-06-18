import { useEffect, useState } from "react";
import { apiConfig } from "../config/api.config";

const API_URL = apiConfig.baseUrl;

export const useLegacyPlayers = () => {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const fetchPlayers = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`${API_URL}/legacy-players`);
        if (!response.ok) {
          throw new Error("Failed to fetch player list");
        }
        const data = await response.json();
        if (!cancelled) {
          setPlayers(data.players || []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchPlayers();

    return () => {
      cancelled = true;
    };
  }, []);

  return { players, loading, error };
};

export default useLegacyPlayers;
