import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';

const SheetSyncContext = createContext();

export const useSheetSync = () => {
  return useContext(SheetSyncContext);
};

export const SheetSyncProvider = ({ children }) => {
  const [sheetUrl, setSheetUrl] = useState('');
  const [syncStatus, setSyncStatus] = useState('idle'); // idle, connecting, syncing, error, success
  const [lastSync, setLastSync] = useState(null);
  const [syncInterval, setSyncInterval] = useState(30); // seconds
  const [autoSync, setAutoSync] = useState(false);
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
      setSyncData(sheetResponse.data || []);

      setLastSync(new Date());
      setSyncStatus('success');
      setTimeout(() => setSyncStatus('idle'), 2000);

    } catch (err) {
      setError(err.message);
      setSyncStatus('error');
      setTimeout(() => setSyncStatus('idle'), 3000);
    }
  }, [sheetUrl]);

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
