import { apiConfig } from "../config/api.config";
import { fetchJson } from "./fetchJson";

const API_URL = apiConfig.baseUrl;

const roundFetchJson = async (path, getAccessToken, options = {}) => {
  const token = await getAccessToken();
  return fetchJson(`${API_URL}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });
};

export const postMyRound = (getAccessToken, round) => roundFetchJson(
  "/players/me/round",
  getAccessToken,
  {
    method: "POST",
    body: JSON.stringify(round),
  },
);

export const fetchMyRounds = (getAccessToken) => roundFetchJson(
  "/players/me/rounds",
  getAccessToken,
);

export const fetchPendingAttestations = (getAccessToken) => roundFetchJson(
  "/rounds/pending-attestation",
  getAccessToken,
);

export const attestRound = (getAccessToken, roundId) => roundFetchJson(
  `/rounds/${roundId}/attest`,
  getAccessToken,
  { method: "POST" },
);
