import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';

const SheetSyncContext = createContext();

export const useSheetSync = () => {
  return useContext(SheetSyncContext);
};

export const SheetSyncProvider = ({ children }) => {
  // Hardcode the Wolf-Goat-Pig Google Sheets URL
  const [sheetUrl, setSheetUrl] = useState('https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/edit?pli=1&gid=0#gid=0');
  const [syncStatus, setSyncStatus] = useState('idle'); // idle, connecting, syncing, error, success
  const [lastSync, setLastSync] = useState(null);
  const [syncInterval, setSyncInterval] = useState(30); // seconds
  const [autoSync, setAutoSync] = useState(true); // Enable auto sync by default
  const [syncData, setSyncData] = useState([]);
  const [error, setError] = useState(null);

  const extractSheetId = (url) => {
    const patterns = [
      /\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/,
      /^([a-zA-Z0-9-_]+)$/
    ];
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) return match[1];
    }
    return null;
  };

  const buildCsvUrl = (sheetId, gid = '0') => {
    return `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=csv&gid=${gid}`;
  };

  const parseSheetUrl = (url) => {
    const sheetId = extractSheetId(url);
    if (!sheetId) return null;
    const gidMatch = url.match(/gid=(\d+)/);
    const gid = gidMatch ? gidMatch[1] : '0';
    return { sheetId, gid };
  };

  const fetchSheetData = async (csvUrl) => {
    const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
    const response = await fetch(`${API_URL}/sheet-integration/fetch-google-sheet`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ csv_url: csvUrl })
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to fetch sheet data: ${errorText}`);
    }
    return response.json();
  };

  const performLiveSync = useCallback(async (manualSheetUrl = null) => {
    const currentSheetUrl = manualSheetUrl || sheetUrl;
    if (!currentSheetUrl) return;

    try {
      setSyncStatus('connecting');
      setError(null);

      const urlInfo = parseSheetUrl(currentSheetUrl);
      if (!urlInfo) {
        throw new Error('Invalid Google Sheets URL');
      }

      const csvUrl = buildCsvUrl(urlInfo.sheetId, urlInfo.gid);

      setSyncStatus('syncing');

      const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/sheet-integration/sync-wgp-sheet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ csv_url: csvUrl })
      });

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.statusText}`);
      }

      await response.json();

      const sheetResponse = await fetchSheetData(csvUrl);
      
      // Transform the Google Sheets data to match leaderboard format
      const transformedData = (sheetResponse.data || []).map((row, index) => {
        // Aggregate scores by player
        const playerName = row.Member || row['Player'] || '';
        const score = parseInt(row.Score) || 0;
        
        return {
          id: `player-${index}`,
          player_name: playerName,
          name: playerName,
          total_earnings: score,
          score: score,
          games_played: 1, // Each row represents a game
          total_games: 1,
          win_percentage: score > 0 ? 100 : 0,
          last_played: row.Date || 'N/A'
        };
      }).filter(player => player.player_name); // Filter out empty rows
      
      // Aggregate by player name
      const aggregatedData = {};
      transformedData.forEach(player => {
        if (player.player_name) {
          if (!aggregatedData[player.player_name]) {
            aggregatedData[player.player_name] = {
              ...player,
              total_earnings: 0,
              games_played: 0,
              wins: 0
            };
          }
          aggregatedData[player.player_name].total_earnings += player.total_earnings;
          aggregatedData[player.player_name].games_played += 1;
          if (player.total_earnings > 0) {
            aggregatedData[player.player_name].wins += 1;
          }
          aggregatedData[player.player_name].last_played = player.last_played;
        }
      });
      
      // Calculate win percentage
      const finalData = Object.values(aggregatedData).map((player, index) => ({
        ...player,
        id: `player-${index}`,
        total_games: player.games_played,
        win_percentage: player.games_played > 0 ? (player.wins / player.games_played) * 100 : 0
      }));
      
      setSyncData(finalData);

      setLastSync(new Date());
      setSyncStatus('success');
      setTimeout(() => setSyncStatus('idle'), 2000);

    } catch (err) {
      setError(err.message);
      setSyncStatus('error');
      setTimeout(() => setSyncStatus('idle'), 3000);
    }
  }, [sheetUrl]);

  // Initial sync on load
  useEffect(() => {
    if (sheetUrl) {
      performLiveSync();
    }
  }, []); // Only run once on mount

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
    error,
    performLiveSync,
  };

  return (
    <SheetSyncContext.Provider value={value}>
      {children}
    </SheetSyncContext.Provider>
  );
};
