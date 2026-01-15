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
  const [syncInterval, setSyncInterval] = useState(300); // seconds (5 minutes default)
  const [autoSync, setAutoSync] = useState(false); // Disable auto sync by default to reduce API calls
  const [syncData, setSyncData] = useState([]);
  const [error, setError] = useState(null);

  const extractSheetId = useCallback((url) => {
    // Ensure url is a string
    if (!url || typeof url !== 'string') {
      console.error('extractSheetId: URL is not a string:', url, typeof url);
      return null;
    }
    
    const patterns = [
      /\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/,
      /^([a-zA-Z0-9-_]+)$/
    ];
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        return match[1];
      }
    }
    console.error('extractSheetId: No pattern matched for URL:', url);
    return null;
  }, []);

  const buildCsvUrl = (sheetId, gid = '0') => {
    return `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=csv&gid=${gid}`;
  };

  const parseSheetUrl = useCallback((url) => {
    // Ensure url is a string
    if (!url || typeof url !== 'string') {
      return null;
    }
    
    const sheetId = extractSheetId(url);
    if (!sheetId) return null;
    const gidMatch = url.match(/gid=(\d+)/);
    const gid = gidMatch ? gidMatch[1] : '0';
    return { sheetId, gid };
  }, [extractSheetId]);

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
    
    if (process.env.NODE_ENV !== 'production') {
      console.debug('performLiveSync called with:', { manualSheetUrl, sheetUrl, currentSheetUrl });
    }
    
    if (!currentSheetUrl) {
      console.error('No sheet URL available for sync');
      return;
    }

    try {
      setSyncStatus('connecting');
      setError(null);

      const urlInfo = parseSheetUrl(currentSheetUrl);
      
      if (!urlInfo) {
        console.error('Failed to parse Google Sheets URL:', currentSheetUrl);
        throw new Error(`Invalid Google Sheets URL: ${currentSheetUrl}`);
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

      // Helper to find column value by trying multiple possible header names (case-insensitive)
      const getColumnValue = (row, possibleNames) => {
        for (const name of possibleNames) {
          // Try exact match first
          if (row[name] !== undefined) return row[name];
          // Try case-insensitive match
          const key = Object.keys(row).find(k => k.toLowerCase() === name.toLowerCase());
          if (key && row[key] !== undefined) return row[key];
        }
        return null;
      };

      // Transform the Google Sheets data to match leaderboard format
      const transformedData = (sheetResponse.data || []).map((row, index) => {
        // Get player name (try multiple column name variations)
        const playerName = getColumnValue(row, ['Member', 'Player', 'Name', 'Golfer']) || '';

        // Get score (try multiple column name variations)
        const scoreStr = getColumnValue(row, ['Score', 'Quarters', 'Sum Score', 'Total Score', 'Total', 'Points']);
        const score = scoreStr ? parseInt(scoreStr) || 0 : 0;

        // Get date
        const dateValue = getColumnValue(row, ['Date', 'Game Date', 'Played']) || 'N/A';

        // Skip header rows or summary rows
        if (!playerName ||
            playerName.toLowerCase() === 'member' ||
            playerName.toLowerCase() === 'player' ||
            playerName.toLowerCase() === 'total' ||
            playerName.toLowerCase().includes('most rounds') ||
            playerName.toLowerCase().includes('top 5')) {
          return null;
        }

        return {
          id: `player-${index}`,
          player_name: playerName,
          name: playerName,
          total_earnings: score,
          score: score,
          games_played: 1, // Each row represents a game
          total_games: 1,
          win_percentage: score > 0 ? 100 : 0,
          last_played: dateValue
        };
      }).filter(player => player && player.player_name); // Filter out empty/null rows

      // Aggregate by player name
      const aggregatedData = {};
      transformedData.forEach(player => {
        if (player.player_name) {
          if (!aggregatedData[player.player_name]) {
            aggregatedData[player.player_name] = {
              ...player,
              total_earnings: 0,
              games_played: 0,
              wins: 0,
              last_played: null
            };
          }
          aggregatedData[player.player_name].total_earnings += player.total_earnings;
          aggregatedData[player.player_name].games_played += 1;
          if (player.total_earnings > 0) {
            aggregatedData[player.player_name].wins += 1;
          }

          // Keep the most recent date
          const currentDate = player.last_played;
          const existingDate = aggregatedData[player.player_name].last_played;

          if (currentDate && currentDate !== 'N/A') {
            if (!existingDate || existingDate === 'N/A') {
              aggregatedData[player.player_name].last_played = currentDate;
            } else {
              try {
                const current = new Date(currentDate);
                const existing = new Date(existingDate);
                if (!isNaN(current.getTime()) && !isNaN(existing.getTime())) {
                  aggregatedData[player.player_name].last_played = current > existing ? currentDate : existingDate;
                } else {
                  // If either date is invalid, keep the existing one
                  aggregatedData[player.player_name].last_played = existingDate;
                }
              } catch (e) {
                // If date parsing fails, just use the current value
                aggregatedData[player.player_name].last_played = currentDate;
              }
            }
          }
        }
      });

      // Calculate win percentage
      const finalData = Object.values(aggregatedData).map((player, index) => ({
        ...player,
        id: `player-${index}`,
        total_games: player.games_played,
        win_percentage: player.games_played > 0 ? (player.wins / player.games_played) * 100 : 0
      }));

      console.log('Leaderboard data transformed:', {
        headers: sheetResponse.headers,
        rowCount: sheetResponse.row_count,
        playersFound: finalData.length,
        sampleData: finalData.slice(0, 3),
        rawDataSample: (sheetResponse.data || []).slice(0, 2) // Show raw data to debug column names
      });

      setSyncData(finalData);

      setLastSync(new Date());
      setSyncStatus('success');
      setTimeout(() => setSyncStatus('idle'), 2000);

    } catch (err) {
      console.error('Google Sheets sync error:', err);
      setError(err.message || 'Unknown sync error occurred');
      setSyncStatus('error');
      setTimeout(() => setSyncStatus('idle'), 3000);
    }
  }, [parseSheetUrl, sheetUrl]);

  // Initial sync on load - fetch once when component mounts
  useEffect(() => {
    if (sheetUrl && syncData.length === 0 && syncStatus === 'idle') {
      performLiveSync();
    }
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
    error,
    performLiveSync,
  };

  return (
    <SheetSyncContext.Provider value={value}>
      {children}
    </SheetSyncContext.Provider>
  );
};
