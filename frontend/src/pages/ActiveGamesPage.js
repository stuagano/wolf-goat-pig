// frontend/src/pages/ActiveGamesPage.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui';
import { useTheme } from '../theme/Provider';
import CommissionerChat from '../components/CommissionerChat';

const API_URL = process.env.REACT_APP_API_URL || "";

/**
 * ActiveGamesPage - List all in-progress games
 * Allows users to view and rejoin active games
 */
const ActiveGamesPage = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('in_progress'); // in_progress, setup, all
  const [currentPage, setCurrentPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const LIMIT = 10;

  // Load games
  useEffect(() => {
    loadGames();
  }, [filter, currentPage]);

  const loadGames = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        limit: LIMIT,
        offset: currentPage * LIMIT
      });

      if (filter !== 'all') {
        params.append('status', filter);
      }

      const response = await fetch(`${API_URL}/games?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Failed to load games: ${response.statusText}`);
      }

      const data = await response.json();
      setGames(data.games || []);
      setTotalCount(data.total_count || 0);
      setHasMore(data.has_more || false);
    } catch (err) {
      console.error('Error loading games:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinGame = (gameId, joinCode) => {
    // Navigate to join page with pre-filled code
    navigate(`/join?code=${joinCode}`);
  };

  const handleResumeGame = (gameId) => {
    // Navigate directly to game page
    navigate(`/game/${gameId}`);
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'Unknown';
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch (e) {
      return isoString;
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      setup: { color: '#F59E0B', icon: '⚙️', label: 'Setup' },
      in_progress: { color: '#10B981', icon: '🎮', label: 'In Progress' },
      completed: { color: '#6B7280', icon: '✅', label: 'Completed' }
    };

    const badge = badges[status] || badges.setup;

    return (
      <span style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '4px 12px',
        borderRadius: '12px',
        background: `${badge.color}20`,
        color: badge.color,
        fontSize: '12px',
        fontWeight: '600'
      }}>
        <span>{badge.icon}</span>
        {badge.label}
      </span>
    );
  };

  if (loading && games.length === 0) {
    return (
      <div style={{
        minHeight: '100vh',
        padding: '20px',
        background: theme.colors.background,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Card style={{ maxWidth: '500px', textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '24px' }}>🎮</div>
          <h2 style={{ marginTop: 0, marginBottom: '16px', color: theme.colors.primary }}>
            Loading Games...
          </h2>
          <div style={{
            display: 'inline-block',
            width: '40px',
            height: '40px',
            border: `4px solid ${theme.colors.border}`,
            borderTop: `4px solid ${theme.colors.primary}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
        </Card>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      padding: '20px',
      background: theme.colors.background
    }}>
      <div style={{ maxWidth: '1000px', margin: '0 auto', paddingTop: '60px' }}>
        {/* Header */}
        <div style={{
          textAlign: 'center',
          marginBottom: '40px'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎮</div>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: theme.colors.primary,
            marginBottom: '12px'
          }}>
            Active Games
          </h1>
          <p style={{
            color: theme.colors.textSecondary,
            fontSize: '1.1rem'
          }}>
            {totalCount} {filter === 'all' ? '' : filter.replace('_', ' ')} game{totalCount !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Filter Tabs */}
        <Card style={{ marginBottom: '30px', padding: '12px' }}>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { value: 'in_progress', label: '🎮 In Progress', icon: '🎮' },
              { value: 'setup', label: '⚙️ Setup', icon: '⚙️' },
              { value: 'all', label: '📋 All Games', icon: '📋' }
            ].map(tab => (
              <button
                key={tab.value}
                onClick={() => {
                  setFilter(tab.value);
                  setCurrentPage(0);
                }}
                style={{
                  ...theme.buttonStyle,
                  background: filter === tab.value ? theme.colors.primary : 'transparent',
                  color: filter === tab.value ? 'white' : theme.colors.text,
                  border: `2px solid ${filter === tab.value ? theme.colors.primary : theme.colors.border}`,
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '600'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </Card>

        {/* Error Display */}
        {error && (
          <Card variant="error" style={{ marginBottom: '30px' }}>
            <h3 style={{ marginTop: 0, marginBottom: '12px', color: theme.colors.error }}>
              ❌ Error
            </h3>
            <p style={{ marginBottom: '16px' }}>{error}</p>
            <button
              style={{
                ...theme.buttonStyle,
                padding: '12px 24px'
              }}
              onClick={loadGames}
            >
              Retry
            </button>
          </Card>
        )}

        {/* Games List */}
        {games.length === 0 && !loading ? (
          <Card style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ fontSize: '64px', marginBottom: '24px' }}>🎯</div>
            <h2 style={{ color: theme.colors.primary, marginBottom: '16px' }}>
              No {filter === 'all' ? '' : filter.replace('_', ' ')} games found
            </h2>
            <p style={{ color: theme.colors.textSecondary, marginBottom: '24px' }}>
              {filter === 'in_progress'
                ? "No games are currently in progress. Create a new game to get started!"
                : "There are no games matching your filter criteria."}
            </p>
            <button
              onClick={() => navigate('/game')}
              style={{
                ...theme.buttonStyle,
                background: theme.colors.primary,
                padding: '14px 28px',
                fontSize: '16px'
              }}
            >
              Create New Game
            </button>
          </Card>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {games.map(game => (
              <Card key={game.game_id} style={{ padding: '24px' }}>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr auto',
                  gap: '20px',
                  alignItems: 'start'
                }}>
                  {/* Game Info */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                      {getStatusBadge(game.game_status)}
                      <span style={{
                        fontSize: '12px',
                        color: theme.colors.textSecondary
                      }}>
                        Created {formatDate(game.created_at)}
                      </span>
                    </div>

                    <h3 style={{
                      margin: '0 0 8px 0',
                      color: theme.colors.text,
                      fontSize: '18px',
                      fontWeight: '600'
                    }}>
                      Game #{game.game_id.slice(0, 8)}
                    </h3>

                    <div style={{
                      display: 'flex',
                      gap: '16px',
                      flexWrap: 'wrap',
                      fontSize: '14px',
                      color: theme.colors.textSecondary
                    }}>
                      {game.join_code && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span>🔑</span>
                          <span>Code: <strong style={{ color: theme.colors.text }}>{game.join_code}</strong></span>
                        </div>
                      )}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span>👥</span>
                        <span>{game.player_count} player{game.player_count !== 1 ? 's' : ''}</span>
                      </div>
                      {game.updated_at && game.updated_at !== game.created_at && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span>🔄</span>
                          <span>Updated {formatDate(game.updated_at)}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: '8px', flexDirection: 'column', minWidth: '140px' }}>
                    {game.game_status === 'in_progress' && (
                      <button
                        onClick={() => handleResumeGame(game.game_id)}
                        style={{
                          ...theme.buttonStyle,
                          background: '#10B981',
                          padding: '10px 20px',
                          fontSize: '14px',
                          fontWeight: '600',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        ▶️ Resume
                      </button>
                    )}
                    {game.game_status === 'setup' && game.join_code && (
                      <button
                        onClick={() => handleJoinGame(game.game_id, game.join_code)}
                        style={{
                          ...theme.buttonStyle,
                          background: '#0369A1',
                          padding: '10px 20px',
                          fontSize: '14px',
                          fontWeight: '600',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        🔗 Join
                      </button>
                    )}
                    <button
                      onClick={() => navigate(`/game/${game.game_id}`)}
                      style={{
                        ...theme.buttonStyle,
                        background: 'transparent',
                        color: theme.colors.text,
                        border: `2px solid ${theme.colors.border}`,
                        padding: '10px 20px',
                        fontSize: '14px',
                        fontWeight: '600'
                      }}
                    >
                      👁️ View
                    </button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Pagination */}
        {(currentPage > 0 || hasMore) && (
          <Card style={{ marginTop: '30px', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
                disabled={currentPage === 0}
                style={{
                  ...theme.buttonStyle,
                  background: currentPage === 0 ? theme.colors.border : theme.colors.primary,
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '600',
                  opacity: currentPage === 0 ? 0.5 : 1,
                  cursor: currentPage === 0 ? 'not-allowed' : 'pointer'
                }}
              >
                ← Previous
              </button>

              <span style={{ color: theme.colors.textSecondary, fontSize: '14px' }}>
                Page {currentPage + 1} {hasMore ? `• ${totalCount} total` : '• Last page'}
              </span>

              <button
                onClick={() => setCurrentPage(p => p + 1)}
                disabled={!hasMore}
                style={{
                  ...theme.buttonStyle,
                  background: !hasMore ? theme.colors.border : theme.colors.primary,
                  padding: '10px 20px',
                  fontSize: '14px',
                  fontWeight: '600',
                  opacity: !hasMore ? 0.5 : 1,
                  cursor: !hasMore ? 'not-allowed' : 'pointer'
                }}
              >
                Next →
              </button>
            </div>
          </Card>
        )}

        {/* Quick Actions */}
        <Card style={{ marginTop: '30px', textAlign: 'center', padding: '30px' }}>
          <h3 style={{ color: theme.colors.primary, marginBottom: '20px' }}>
            Quick Actions
          </h3>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => navigate('/game')}
              style={{
                ...theme.buttonStyle,
                background: '#047857',
                padding: '12px 24px',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              🎮 Create New Game
            </button>
            <button
              onClick={() => navigate('/join')}
              style={{
                ...theme.buttonStyle,
                background: '#0369A1',
                padding: '12px 24px',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              🔗 Join with Code
            </button>
            <button
              onClick={() => navigate('/')}
              style={{
                ...theme.buttonStyle,
                background: 'transparent',
                color: theme.colors.text,
                border: `2px solid ${theme.colors.border}`,
                padding: '12px 24px',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              🏠 Back to Home
            </button>
          </div>
        </Card>
      </div>
      <CommissionerChat gameState={null} />
    </div>
  );
};

export default ActiveGamesPage;
