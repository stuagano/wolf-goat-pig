import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import './DatabaseMigrations.css';

const DatabaseMigrations = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [adminKey, setAdminKey] = useState(localStorage.getItem('adminKey') || '');
  const [logs, setLogs] = useState([]);
  const { user } = useAuth0();

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
  };

  const fetchStatus = async () => {
    if (!adminKey) {
      setError('Please enter admin key');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/migrations/status`, {
        headers: {
          'X-Admin-Key': adminKey
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setStatus(data);
      addLog('Schema status loaded successfully', 'success');

      // Save admin key if successful
      localStorage.setItem('adminKey', adminKey);
    } catch (err) {
      setError(err.message);
      addLog(`Error: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const runMigration = async (migrationName) => {
    if (!adminKey) {
      setError('Please enter admin key');
      return;
    }

    // eslint-disable-next-line no-restricted-globals
    if (!confirm(`Run migration: ${migrationName}?`)) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/migrations/run?migration_name=${migrationName}`,
        {
          method: 'POST',
          headers: {
            'X-Admin-Key': adminKey
          }
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      addLog(`Migration ${migrationName} completed`, 'success');

      if (data.changes && data.changes.length > 0) {
        data.changes.forEach(change => addLog(`  - ${change}`, 'info'));
      }

      // Refresh status
      await fetchStatus();
    } catch (err) {
      setError(err.message);
      addLog(`Error running ${migrationName}: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const runAllMigrations = async () => {
    if (!adminKey) {
      setError('Please enter admin key');
      return;
    }

    // eslint-disable-next-line no-restricted-globals
    if (!confirm('Run ALL pending migrations? This will apply all schema changes.')) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/migrations/run-all`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      addLog('All migrations completed', 'success');

      if (data.migrations_applied && data.migrations_applied.length > 0) {
        data.migrations_applied.forEach(migration =>
          addLog(`  - Applied: ${migration}`, 'info')
        );
      } else {
        addLog('  - No migrations were needed', 'info');
      }

      // Refresh status
      await fetchStatus();
    } catch (err) {
      setError(err.message);
      addLog(`Error running all migrations: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const availableMigrations = [
    { name: 'add_tee_order', description: 'Add tee_order column to game_players' },
    { name: 'add_game_id', description: 'Add game_id column to game_state' },
    { name: 'add_timestamps', description: 'Add created_at/updated_at columns' },
    { name: 'add_join_code', description: 'Add join_code column to game_state' },
    { name: 'add_creator_user_id', description: 'Add creator_user_id column to game_state' },
    { name: 'add_game_status', description: 'Add game_status column to game_state' }
  ];

  useEffect(() => {
    if (adminKey) {
      fetchStatus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="database-migrations">
      <div className="migrations-header">
        <h1>Database Migrations</h1>
        <p className="subtitle">Manage database schema changes</p>
      </div>

      {user && (
        <div className="user-info">
          Logged in as: <strong>{user.username}</strong>
        </div>
      )}

      <div className="admin-key-section">
        <div className="input-group">
          <label htmlFor="adminKey">Admin Key:</label>
          <input
            id="adminKey"
            type="password"
            value={adminKey}
            onChange={(e) => setAdminKey(e.target.value)}
            placeholder="Enter admin key"
            className="admin-key-input"
          />
          <button
            onClick={fetchStatus}
            disabled={loading || !adminKey}
            className="btn-primary"
          >
            {loading ? 'Loading...' : 'Load Status'}
          </button>
        </div>
        <p className="admin-key-hint">
          Use ADMIN_KEY from environment or "dev-admin-key-INSECURE" in development
        </p>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {status && (
        <>
          <div className="schema-status">
            <h2>Current Schema Status</h2>

            <div className="tables-list">
              <h3>All Tables ({status.all_tables?.length || 0})</h3>
              <div className="table-chips">
                {status.all_tables?.map(table => (
                  <span key={table} className="chip">{table}</span>
                ))}
              </div>
            </div>

            {status.critical_tables && Object.keys(status.critical_tables).length > 0 && (
              <div className="critical-tables">
                <h3>Critical Tables Detail</h3>
                {Object.entries(status.critical_tables).map(([tableName, tableInfo]) => (
                  <div key={tableName} className="table-detail">
                    <h4>{tableName}</h4>
                    <div className="columns-section">
                      <strong>Columns ({tableInfo.columns.length}):</strong>
                      <div className="column-chips">
                        {tableInfo.columns.map(col => (
                          <span key={col} className="chip chip-column">{col}</span>
                        ))}
                      </div>
                    </div>
                    {tableInfo.indexes && tableInfo.indexes.length > 0 && (
                      <div className="indexes-section">
                        <strong>Indexes ({tableInfo.indexes.length}):</strong>
                        <div className="column-chips">
                          {tableInfo.indexes.map(idx => (
                            <span key={idx} className="chip chip-index">{idx}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="migrations-actions">
            <h2>Available Migrations</h2>

            <div className="migration-buttons">
              <button
                onClick={runAllMigrations}
                disabled={loading}
                className="btn-run-all"
              >
                🚀 Run All Migrations
              </button>
            </div>

            <div className="migrations-list">
              {availableMigrations.map(migration => (
                <div key={migration.name} className="migration-item">
                  <div className="migration-info">
                    <strong>{migration.name}</strong>
                    <p>{migration.description}</p>
                  </div>
                  <button
                    onClick={() => runMigration(migration.name)}
                    disabled={loading}
                    className="btn-run"
                  >
                    Run
                  </button>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {logs.length > 0 && (
        <div className="logs-section">
          <h2>Activity Log</h2>
          <div className="logs-container">
            {logs.map((log, idx) => (
              <div key={idx} className={`log-entry log-${log.type}`}>
                <span className="log-timestamp">{log.timestamp}</span>
                <span className="log-message">{log.message}</span>
              </div>
            ))}
          </div>
          <button
            onClick={() => setLogs([])}
            className="btn-clear-logs"
          >
            Clear Logs
          </button>
        </div>
      )}

      <div className="warning-section">
        <h3>⚠️ Warning</h3>
        <p>
          This interface allows direct database schema modifications.
          Always backup your data before running migrations in production.
        </p>
        <p>
          Migrations are designed to be idempotent (safe to run multiple times).
        </p>
      </div>
    </div>
  );
};

export default DatabaseMigrations;
