import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { apiConfig } from "../config/api.config";
import { acquireAccessToken, apiTokenOptions } from "../services/authToken";

const API_URL = apiConfig.baseUrl;
const PROFILE_UPDATED_EVENT = "wgp:player-profile-updated";
const LEGACY_SKIP_UPDATED_EVENT = "wgp:legacy-name-skip-updated";

/**
 * Hook to manage current user's player profile
 * Handles fetching profile, checking onboarding status, and updating legacy_name
 */
export const usePlayerProfile = () => {
  const { isAuthenticated, getAccessTokenSilently, user } = useAuth0();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [legacyNameSuggestion, setLegacyNameSuggestion] = useState(null);
  const [legacyNameSkipped, setLegacyNameSkipped] = useState(false);
  const profileRequestId = useRef(0);
  const isUnlinked = Boolean(profile && !profile.legacy_name);
  // ponytail: linking is optional; never block new users with the onboarding modal
  const needsLegacyName = false;
  const userSub = user?.sub || null;
  const legacyNameSkipKey = userSub ? `legacy_name_skipped:${userSub}` : null;

  // Fetch current user's profile
  const fetchProfile = useCallback(async () => {
    const requestId = ++profileRequestId.current;

    if (!isAuthenticated || !userSub) {
      setProfile(null);
      setLegacyNameSuggestion(null);
      setLegacyNameSkipped(false);
      setError(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const token = await acquireAccessToken(getAccessTokenSilently, apiTokenOptions);

      const response = await fetch(`${API_URL}/players/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch profile: ${response.status}`);
      }

      const data = await response.json();
      if (requestId !== profileRequestId.current) return;

      setProfile(data);

      const skipped = Boolean(localStorage.getItem(legacyNameSkipKey));
      setLegacyNameSkipped(!data.legacy_name && skipped);

      // Fuzzy legacy-name match to SUGGEST during onboarding. This is NOT an
      // auto-link — the account stays unlinked until the user confirms it.
      setLegacyNameSuggestion(data.legacy_name_suggestion || null);

      setError(null);
    } catch (err) {
      if (requestId !== profileRequestId.current) return;

      console.error("Error fetching profile:", err);
      setError(err.message);
    } finally {
      if (requestId === profileRequestId.current) {
        setLoading(false);
      }
    }
  }, [isAuthenticated, getAccessTokenSilently, legacyNameSkipKey, userSub]);

  // Update the user's legacy name
  const updateLegacyName = useCallback(
    async (legacyName) => {
      if (!isAuthenticated || !userSub) {
        throw new Error("Not authenticated");
      }

      try {
        const token = await acquireAccessToken(getAccessTokenSilently, apiTokenOptions);

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
        setLegacyNameSkipped(false);
        setLegacyNameSuggestion(null);
        localStorage.removeItem(legacyNameSkipKey);
        window.dispatchEvent(new CustomEvent(PROFILE_UPDATED_EVENT, {
          detail: { userSub, profile: updatedProfile },
        }));

        return updatedProfile;
      } catch (err) {
        console.error("Error updating legacy name:", err);
        throw err;
      }
    },
    [isAuthenticated, getAccessTokenSilently, legacyNameSkipKey, userSub],
  );

  // Skip legacy name selection (user says "I'm not in the list")
  const skipLegacyName = useCallback(() => {
    if (!legacyNameSkipKey || !userSub) return;

    localStorage.setItem(legacyNameSkipKey, "true");
    setLegacyNameSkipped(true);
    window.dispatchEvent(new CustomEvent(LEGACY_SKIP_UPDATED_EVENT, {
      detail: { userSub, skipped: true },
    }));
  }, [legacyNameSkipKey, userSub]);

  // Reset skip status (if user wants to try again later)
  const resetSkip = useCallback(() => {
    if (!legacyNameSkipKey || !userSub) return;

    localStorage.removeItem(legacyNameSkipKey);
    setLegacyNameSkipped(false);
    window.dispatchEvent(new CustomEvent(LEGACY_SKIP_UPDATED_EVENT, {
      detail: { userSub, skipped: false },
    }));
  }, [legacyNameSkipKey, userSub]);

  // Multiple screens use this hook at once (the app-level onboarding wrapper,
  // Home, Signup, and Account). Keep their local state synchronized in the
  // current tab; the browser's native `storage` event does not fire in the tab
  // that made the change.
  useEffect(() => {
    const handleProfileUpdated = (event) => {
      if (event.detail?.userSub !== userSub) return;
      profileRequestId.current += 1;
      setProfile(event.detail.profile);
      setLegacyNameSuggestion(event.detail.profile?.legacy_name_suggestion || null);
      if (event.detail.profile?.legacy_name) {
        setLegacyNameSkipped(false);
      }
    };
    const handleSkipUpdated = (event) => {
      if (event.detail?.userSub !== userSub) return;
      setLegacyNameSkipped(Boolean(event.detail.skipped));
    };

    window.addEventListener(PROFILE_UPDATED_EVENT, handleProfileUpdated);
    window.addEventListener(LEGACY_SKIP_UPDATED_EVENT, handleSkipUpdated);
    return () => {
      window.removeEventListener(PROFILE_UPDATED_EVENT, handleProfileUpdated);
      window.removeEventListener(LEGACY_SKIP_UPDATED_EVENT, handleSkipUpdated);
    };
  }, [userSub]);

  useEffect(() => {
    fetchProfile();
    return () => {
      profileRequestId.current += 1;
    };
  }, [fetchProfile]);

  return {
    profile,
    loading,
    error,
    needsLegacyName,
    legacyNameSkipped,
    legacyNameSuggestion,
    role: profile?.role || null,
    isSuperAdmin: profile ? !!profile.is_super_admin : null,
    // Compatibility alias for existing admin screens.
    isAdmin: profile ? !!profile.is_super_admin : null,
    updateLegacyName,
    skipLegacyName,
    resetSkip,
    refetch: fetchProfile,
  };
};

export default usePlayerProfile;
