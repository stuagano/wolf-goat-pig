// frontend/src/pages/CompletedGamesPage.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui';
import { useTheme } from '../theme/Provider';
import CommissionerChat from '../components/CommissionerChat';

const API_URL = process.env.REACT_APP_API_URL || "";

/**
 * CompletedGamesPage - List all completed games with results
 * Shows game history with winner information and final scores
 */
const CompletedGamesPage = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const LIMIT = 10;

  // Load completed games
  useEffect(() => {
    loadGames();
  }, [currentPage]);

  const loadGames = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        status: 'completed',
        limit: LIMIT,
        offset: currentPage * LIMIT
      });

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

  const handleViewGame = (gameId) => {
    navigate(`/game/${gameId}`);
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'Unknown';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return isoString;
    }
  };

  const formatDuration = (createdAt, updatedAt) => {
    if (!createdAt || !updatedAt) return null;
    try {
      const start = new Date(createdAt);
      const end = new Date(updatedAt);
      const diffMs = end - start;
      const diffMins = Math.floor(diffMs / 60000);
      const hours = Math.floor(diffMins / 60);
      const mins = diffMins % 60;

      if (hours > 0) {
        return `${hours}h ${mins}m`;
      }
      return `${mins}m`;
    } catch (e) {
      return null;
    }
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
          <div style={{ fontSize: '48px', marginBottom: '24px' }}>🏆</div>
          <h2 style={{ marginTop: 0, marginBottom: '16px', color: theme.colors.primary }}>
            Loading Game History...
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
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🏆</div>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: theme.colors.primary,
            marginBottom: '12px'
          }}>
            Game History
          </h1>
          <p style={{
            color: theme.colors.textSecondary,
            fontSize: '1.1rem'
          }}>
            {totalCount} completed game{totalCount !== 1 ? 's' : ''}
          </p>
        </div>

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
            <div style={{ fontSize: '64px', marginBottom: '24px' }}>📜</div>
            <h2 style={{ color: theme.colors.primary, marginBottom: '16px' }}>
              No Completed Games
            </h2>
            <p style={{ color: theme.colors.textSecondary, marginBottom: '24px' }}>
              Complete some games to see them appear here!
            </p>
            <button
              onClick={() => navigate('/games/active')}
              style={{
                ...theme.buttonStyle,
                background: theme.colors.primary,
                padding: '14px 28px',
                fontSize: '16px'
              }}
            >
              View Active Games
            </button>
          </Card>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {games.map(game => {
              const duration = formatDuration(game.created_at, game.updated_at);

              return (
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
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '4px 12px',
                          borderRadius: '12px',
                          background: '#10B98120',
                          color: '#10B981',
                          fontSize: '12px',
                          fontWeight: '600'
                        }}>
                          <span>✅</span>
                          Completed
                        </span>
                        <span style={{
                          fontSize: '12px',
                          color: theme.colors.textSecondary
                        }}>
                          {formatDate(game.updated_at || game.created_at)}
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
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span>👥</span>
                          <span>{game.player_count} player{game.player_count !== 1 ? 's' : ''}</span>
                        </div>
                        {duration && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <span>⏱️</span>
                            <span>{duration}</span>
                          </div>
                        )}
                        {game.join_code && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <span>🔑</span>
                            <span>Code: {game.join_code}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', gap: '8px', flexDirection: 'column', minWidth: '140px' }}>
                      <button
                        onClick={() => handleViewGame(game.game_id)}
                        style={{
                          ...theme.buttonStyle,
                          background: theme.colors.primary,
                          padding: '10px 20px',
                          fontSize: '14px',
                          fontWeight: '600',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        📊 View Results
                      </button>
                    </div>
                  </div>
                </Card>
              );
            })}
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
              onClick={() => navigate('/games/active')}
              style={{
                ...theme.buttonStyle,
                background: '#10B981',
                padding: '12px 24px',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              🎮 View Active Games
            </button>
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
              ➕ Create New Game
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

export default CompletedGamesPage;
