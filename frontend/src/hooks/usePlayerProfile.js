import { useState, useEffect, useCallback } from "react";
import { useAuth0 } from "@auth0/auth0-react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

/**
 * Hook to manage current user's player profile
 * Handles fetching profile, checking onboarding status, and updating legacy_name
 */
export const usePlayerProfile = () => {
  const { isAuthenticated, getAccessTokenSilently } = useAuth0();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [needsLegacyName, setNeedsLegacyName] = useState(false);

  // Fetch current user's profile
  const fetchProfile = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const token = await getAccessTokenSilently();

      const response = await fetch(`${API_URL}/players/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch profile: ${response.status}`);
      }

      const data = await response.json();
      setProfile(data);

      // Check if user needs to select their legacy name
      // They need it if: no legacy_name set AND they haven't explicitly skipped
      const skipped = localStorage.getItem("legacy_name_skipped");
      setNeedsLegacyName(!data.legacy_name && !skipped);

      setError(null);
    } catch (err) {
      console.error("Error fetching profile:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, getAccessTokenSilently]);

  // Update the user's legacy name
  const updateLegacyName = useCallback(
    async (legacyName) => {
      if (!isAuthenticated) {
        throw new Error("Not authenticated");
      }

      try {
        const token = await getAccessTokenSilently();

        const response = await fetch(`${API_URL}/players/me/legacy-name`, {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ legacy_name: legacyName }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || `Failed to update: ${response.status}`,
          );
        }

        const updatedProfile = await response.json();
        setProfile(updatedProfile);
        setNeedsLegacyName(false);

        return updatedProfile;
      } catch (err) {
        console.error("Error updating legacy name:", err);
        throw err;
      }
    },
    [isAuthenticated, getAccessTokenSilently],
  );

  // Skip legacy name selection (user says "I'm not in the list")
  const skipLegacyName = useCallback(() => {
    localStorage.setItem("legacy_name_skipped", "true");
    setNeedsLegacyName(false);
  }, []);

  // Reset skip status (if user wants to try again later)
  const resetSkip = useCallback(() => {
    localStorage.removeItem("legacy_name_skipped");
    if (profile && !profile.legacy_name) {
      setNeedsLegacyName(true);
    }
  }, [profile]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  return {
    profile,
    loading,
    error,
    needsLegacyName,
    updateLegacyName,
    skipLegacyName,
    resetSkip,
    refetch: fetchProfile,
  };
};

export default usePlayerProfile;
