// frontend/src/hooks/useAchievements.js
// Post-hole achievement checking — moved verbatim from SimpleScorekeeper.
// Fires the badge-check endpoint per player and surfaces a banner flag when
// any check fails (non-fatal; scoring already succeeded).

import { useState } from "react";
import { apiConfig } from "../config/api.config";
import { triggerBadgeNotification } from "../components/game/BadgeNotification";

const API_URL = apiConfig.baseUrl;

const useAchievements = (players) => {
  // Track achievement check status
  const [achievementCheckFailed, setAchievementCheckFailed] = useState(false);

  // Check achievements for all players and trigger notifications
  const checkAchievements = async () => {
    let failedPlayers = [];
    setAchievementCheckFailed(false);

    for (const player of players) {
      try {
        const response = await fetch(
          `${API_URL}/api/badges/admin/check-achievements/${player.id}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          },
        );

        if (!response.ok) {
          console.warn(
            `Achievement check failed for ${player.name}: ${response.status}`,
          );
          failedPlayers.push(player.name);
          continue;
        }

        const data = await response.json();
        if (!data || typeof data !== "object") {
          console.warn(`Invalid achievement response for ${player.name}`);
          failedPlayers.push(player.name);
          continue;
        }

        // Trigger badge notification for each newly earned badge
        if (
          Array.isArray(data.badges_earned) &&
          data.badges_earned.length > 0
        ) {
          data.badges_earned.forEach((badge) => {
            if (badge && typeof badge === "object") {
              triggerBadgeNotification(badge);
            }
          });
        }
      } catch (err) {
        console.warn(`Achievement check error for ${player.name}:`, err);
        failedPlayers.push(player.name);
      }
    }

    // If any achievements failed to check, set the warning flag
    if (failedPlayers.length > 0) {
      setAchievementCheckFailed(true);
      console.warn(`Achievement check failed for: ${failedPlayers.join(", ")}`);
    }
  };

  return { checkAchievements, achievementCheckFailed, setAchievementCheckFailed };
};

export default useAchievements;
