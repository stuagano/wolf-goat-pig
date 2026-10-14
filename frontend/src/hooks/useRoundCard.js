import { useCallback, useEffect, useState } from "react";
import { apiConfig } from "../config/api.config";
import { useAuthenticatedFetch } from "./useAuthenticatedFetch";

const API_URL = apiConfig.baseUrl;

/**
 * The round's card status from GET /games/{id}/card:
 * { has_photo, can_edit, edited_by, edited_at }.
 * `card` is null when signed out, the response is not OK, or the round is unknown.
 */
export default function useRoundCard(gameId) {
  const authenticatedFetch = useAuthenticatedFetch();
  const [card, setCard] = useState(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (!gameId) {
      setCard(null);
      return undefined;
    }
    let ignore = false;
    authenticatedFetch(`${API_URL}/games/${gameId}/card`)
      .then((res) => (res.ok ? res.json() : null))
      .catch(() => null) // signed out: view-only
      .then((data) => {
        if (!ignore) setCard(data);
      });
    return () => {
      ignore = true;
    };
  }, [gameId, authenticatedFetch, version]);

  const refresh = useCallback(() => setVersion((v) => v + 1), []);

  return { card, refresh };
}
