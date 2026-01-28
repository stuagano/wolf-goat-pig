import React, { useState, useEffect, useMemo } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Component for selecting a legacy player name from the thousand-cranes.com tee sheet
 * Shows a searchable dropdown of all known legacy players
 */
const LegacyNameSelector = ({
  currentName,
  onSelect,
  onSkip,
  suggestedName = null
}) => {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedName, setSelectedName] = useState(suggestedName || '');
  const [isOpen, setIsOpen] = useState(false);

  // Fetch legacy players list
  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const response = await fetch(`${API_URL}/legacy-players`);
        if (!response.ok) {
          throw new Error('Failed to fetch player list');
        }
        const data = await response.json();
        setPlayers(data.players || []);
      } catch (err) {
        console.error('Error fetching legacy players:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPlayers();
  }, []);

  // Filter players based on search query
  const filteredPlayers = useMemo(() => {
    if (!searchQuery.trim()) {
      return players;
    }
    const query = searchQuery.toLowerCase();
    return players.filter(name =>
      name.toLowerCase().includes(query)
    );
  }, [players, searchQuery]);

  const handleSelect = (name) => {
    setSelectedName(name);
    setSearchQuery(name);
    setIsOpen(false);
  };

  const handleConfirm = () => {
    if (selectedName && players.includes(selectedName)) {
      onSelect(selectedName);
    }
  };

  if (loading) {
    return (
      <div className="legacy-name-selector loading">
        <p>Loading player list...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="legacy-name-selector error">
        <p>Error loading players: {error}</p>
        <button onClick={onSkip}>Skip for now</button>
      </div>
    );
  }

  return (
    <div className="legacy-name-selector">
      <div className="selector-header">
        <h3>Link Your Account</h3>
        <p>
          Select your name from the Wing Point Golf tee sheet to sync your signups
          with the existing system.
        </p>
        {currentName && (
          <p className="current-name">
            Signed in as: <strong>{currentName}</strong>
          </p>
        )}
      </div>

      {suggestedName && suggestedName !== selectedName && (
        <div className="suggestion-banner">
          <span>Did you mean </span>
          <button
            className="suggestion-button"
            onClick={() => handleSelect(suggestedName)}
          >
            {suggestedName}
          </button>
          <span>?</span>
        </div>
      )}

      <div className="search-container">
        <input
          type="text"
          placeholder="Search for your name..."
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setIsOpen(true);
            // Clear selection if search doesn't match
            if (selectedName && !e.target.value.toLowerCase().includes(selectedName.toLowerCase())) {
              setSelectedName('');
            }
          }}
          onFocus={() => setIsOpen(true)}
          className="search-input"
        />

        {isOpen && filteredPlayers.length > 0 && (
          <ul className="player-dropdown">
            {filteredPlayers.slice(0, 10).map((name) => (
              <li
                key={name}
                className={`player-option ${name === selectedName ? 'selected' : ''}`}
                onClick={() => handleSelect(name)}
              >
                {name}
              </li>
            ))}
            {filteredPlayers.length > 10 && (
              <li className="more-results">
                +{filteredPlayers.length - 10} more results...
              </li>
            )}
          </ul>
        )}

        {isOpen && searchQuery && filteredPlayers.length === 0 && (
          <div className="no-results">
            No players found matching "{searchQuery}"
          </div>
        )}
      </div>

      <div className="selector-actions">
        <button
          className="confirm-button"
          onClick={handleConfirm}
          disabled={!selectedName || !players.includes(selectedName)}
        >
          Confirm: {selectedName || 'Select a name'}
        </button>

        <button
          className="skip-button"
          onClick={onSkip}
        >
          I'm not in the list (new player)
        </button>
      </div>

      <style jsx>{`
        .legacy-name-selector {
          max-width: 400px;
          margin: 0 auto;
          padding: 20px;
        }

        .selector-header {
          text-align: center;
          margin-bottom: 20px;
        }

        .selector-header h3 {
          margin: 0 0 10px 0;
          color: #2d5a27;
        }

        .selector-header p {
          margin: 0 0 10px 0;
          color: #666;
          font-size: 14px;
        }

        .current-name {
          background: #f0f7ed;
          padding: 8px 12px;
          border-radius: 4px;
          font-size: 13px;
        }

        .suggestion-banner {
          background: #fff3cd;
          border: 1px solid #ffc107;
          padding: 10px 15px;
          border-radius: 4px;
          margin-bottom: 15px;
          text-align: center;
        }

        .suggestion-button {
          background: none;
          border: none;
          color: #0066cc;
          font-weight: bold;
          cursor: pointer;
          text-decoration: underline;
          padding: 0 4px;
        }

        .search-container {
          position: relative;
          margin-bottom: 20px;
        }

        .search-input {
          width: 100%;
          padding: 12px 15px;
          font-size: 16px;
          border: 2px solid #ddd;
          border-radius: 8px;
          box-sizing: border-box;
        }

        .search-input:focus {
          outline: none;
          border-color: #2d5a27;
        }

        .player-dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          max-height: 300px;
          overflow-y: auto;
          background: white;
          border: 1px solid #ddd;
          border-radius: 0 0 8px 8px;
          list-style: none;
          margin: 0;
          padding: 0;
          z-index: 1000;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .player-option {
          padding: 12px 15px;
          cursor: pointer;
          border-bottom: 1px solid #eee;
        }

        .player-option:hover {
          background: #f5f5f5;
        }

        .player-option.selected {
          background: #e8f5e9;
          font-weight: bold;
        }

        .more-results {
          padding: 10px 15px;
          color: #666;
          font-style: italic;
          font-size: 13px;
        }

        .no-results {
          padding: 15px;
          color: #666;
          text-align: center;
          background: #f9f9f9;
          border: 1px solid #ddd;
          border-radius: 0 0 8px 8px;
        }

        .selector-actions {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .confirm-button {
          padding: 14px 20px;
          font-size: 16px;
          font-weight: bold;
          background: #2d5a27;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.2s;
        }

        .confirm-button:hover:not(:disabled) {
          background: #1e3d1a;
        }

        .confirm-button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .skip-button {
          padding: 12px 20px;
          font-size: 14px;
          background: transparent;
          color: #666;
          border: 1px solid #ddd;
          border-radius: 8px;
          cursor: pointer;
        }

        .skip-button:hover {
          background: #f5f5f5;
        }

        .loading, .error {
          text-align: center;
          padding: 40px 20px;
        }

        .error {
          color: #c62828;
        }
      `}</style>
    </div>
  );
};

export default LegacyNameSelector;
