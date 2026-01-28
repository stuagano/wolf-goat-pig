import React, {
  createContext,
  useState,
  useEffect,
  useCallback,
  useContext,
} from "react";

const SheetSyncContext = createContext();

export const useSheetSync = () => {
  return useContext(SheetSyncContext);
};

export const SheetSyncProvider = ({ children }) => {
  // Legacy sheet URL (kept for backward compatibility)
  const [sheetUrl, setSheetUrl] = useState(
    "https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/edit?pli=1&gid=0#gid=0",
  );
  const [syncStatus, setSyncStatus] = useState("idle"); // idle, connecting, syncing, error, success
  const [lastSync, setLastSync] = useState(null);
  const [syncInterval, setSyncInterval] = useState(300); // seconds (5 minutes default)
  const [autoSync, setAutoSync] = useState(false); // Disable auto sync by default to reduce API calls
  const [syncData, setSyncData] = useState([]);
  const [dataStatus, setDataStatus] = useState(null); // Status of all data sources
  const [error, setError] = useState(null);

  /**
   * Fetch unified leaderboard from all data sources.
   * Uses the new /data/leaderboard endpoint which merges:
   * - Primary spreadsheet (read-only legacy data)
   * - Writable spreadsheet (app-entered transition data)
   * - Database (games recorded in the app)
   */
  const performLiveSync = useCallback(async () => {
    try {
      setSyncStatus("connecting");
      setError(null);

      const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

      setSyncStatus("syncing");

      // Fetch unified leaderboard from all sources
      const response = await fetch(`${API_URL}/data/leaderboard?limit=100`);

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.statusText}`);
      }

      const leaderboardData = await response.json();

      // Transform to match existing component expectations
      const finalData = leaderboardData.map((entry, index) => ({
        id: `player-${index}`,
        player_name: entry.member,
        name: entry.member,
        total_earnings: entry.quarters,
        score: entry.quarters,
        games_played: entry.rounds,
        total_games: entry.rounds,
        win_percentage:
          entry.rounds > 0
            ? ((entry.quarters > 0 ? 1 : 0) / entry.rounds) * 100
            : 0,
        best_round: entry.best_round,
        worst_round: entry.worst_round,
        average: entry.average,
        sources: entry.sources,
        last_played: "N/A", // Will be populated when we add round history
      }));

      console.log("Unified leaderboard loaded:", {
        playersFound: finalData.length,
        sampleData: finalData.slice(0, 3),
      });

      setSyncData(finalData);

      // Also fetch data sources status
      try {
        const statusResponse = await fetch(`${API_URL}/data/status`);
        if (statusResponse.ok) {
          const status = await statusResponse.json();
          setDataStatus(status);
          console.log("Data sources status:", status);
        }
      } catch (statusErr) {
        console.warn("Failed to fetch data status:", statusErr);
      }

      setLastSync(new Date());
      setSyncStatus("success");
      setTimeout(() => setSyncStatus("idle"), 2000);
    } catch (err) {
      console.error("Unified data sync error:", err);
      setError(err.message || "Unknown sync error occurred");
      setSyncStatus("error");
      setTimeout(() => setSyncStatus("idle"), 3000);
    }
  }, []);

  // Initial sync on load - fetch once when component mounts
  useEffect(() => {
    if (sheetUrl && syncData.length === 0 && syncStatus === "idle") {
      performLiveSync();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array = run once on mount

  // Auto sync interval
  useEffect(() => {
    let intervalId;
    if (autoSync && sheetUrl && syncInterval > 0) {
      intervalId = setInterval(() => {
        performLiveSync();
      }, syncInterval * 1000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [autoSync, sheetUrl, syncInterval, performLiveSync]);

  const value = {
    sheetUrl,
    setSheetUrl,
    syncStatus,
    lastSync,
    syncInterval,
    setSyncInterval,
    autoSync,
    setAutoSync,
    syncData,
    dataStatus, // Status of all data sources (primary sheet, writable sheet, database)
    error,
    performLiveSync,
  };

  return (
    <SheetSyncContext.Provider value={value}>
      {children}
    </SheetSyncContext.Provider>
  );
};
