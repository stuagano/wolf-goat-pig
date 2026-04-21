import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiConfig } from '../../config/api.config';

const STALE_THRESHOLD_MS = 24 * 60 * 60 * 1000; // 24 hours
const DISMISS_KEY = 'wgp_stale_game_dismissed';

function StaleGameBanner({ isAuthenticated }) {
  const navigate = useNavigate();
  const [staleGames, setStaleGames] = useState([]);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) return;
    if (sessionStorage.getItem(DISMISS_KEY)) {
      setDismissed(true);
      return;
    }

    const fetchStaleGames = async () => {
      try {
        const res = await fetch(`${apiConfig.baseUrl}/games?status=in_progress&limit=10`);
        if (!res.ok) return;
        const data = await res.json();
        const games = data.games || [];
        const now = Date.now();
        const stale = games.filter((g) => {
          const updatedAt = new Date(g.updated_at || g.created_at).getTime();
          return now - updatedAt >= STALE_THRESHOLD_MS;
        });
        setStaleGames(stale);
      } catch {
        // Silently fail — this is a non-critical nudge
      }
    };

    fetchStaleGames();
  }, [isAuthenticated]);

  const handleDismiss = () => {
    sessionStorage.setItem(DISMISS_KEY, '1');
    setDismissed(true);
  };

  if (dismissed || staleGames.length === 0) return null;

  const game = staleGames[0];
  const updatedAt = new Date(game.updated_at || game.created_at);
  const hoursAgo = Math.floor((Date.now() - updatedAt.getTime()) / (1000 * 60 * 60));
  const timeLabel = hoursAgo >= 48
    ? `${Math.floor(hoursAgo / 24)} days ago`
    : `${hoursAgo} hours ago`;

  return (
    <div style={{
      background: 'linear-gradient(135deg, #F97316, #EA580C)',
      borderRadius: '12px',
      padding: '16px 20px',
      marginBottom: '24px',
      boxShadow: '0 4px 6px rgba(249, 115, 22, 0.3)',
      position: 'relative',
    }}>
      {/* Dismiss button */}
      <button
        onClick={handleDismiss}
        aria-label="Dismiss"
        style={{
          position: 'absolute',
          top: '8px',
          right: '12px',
          background: 'none',
          border: 'none',
          color: 'rgba(255, 255, 255, 0.7)',
          fontSize: '18px',
          cursor: 'pointer',
          padding: '4px',
          lineHeight: 1,
        }}
      >
        ✕
      </button>

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'white', marginBottom: '4px' }}>
            {staleGames.length === 1
              ? 'You have an unfinished game'
              : `You have ${staleGames.length} unfinished games`}
          </div>
          <div style={{ color: 'rgba(255, 255, 255, 0.9)', fontSize: '0.9rem' }}>
            Last updated {timeLabel}
            {game.player_count ? ` · ${game.player_count} players` : ''}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
          <button
            onClick={() => navigate(`/game/${game.game_id}`)}
            style={{
              padding: '10px 20px',
              background: 'white',
              color: '#EA580C',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '700',
              cursor: 'pointer',
              transition: 'transform 0.2s',
            }}
            onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
          >
            Resume
          </button>
          {staleGames.length > 1 && (
            <button
              onClick={() => navigate('/games/active')}
              style={{
                padding: '10px 20px',
                background: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                border: '1px solid rgba(255, 255, 255, 0.4)',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'transform 0.2s',
              }}
              onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
              onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
            >
              View All
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default StaleGameBanner;
