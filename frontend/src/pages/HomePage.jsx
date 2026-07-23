import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { LoginButton, AuthHealthCheck } from '../components/auth';
import StaleGameBanner from '../components/game/StaleGameBanner';
import './HomePage.css';

const ADVANCED_TOOLS = [
  { path: '/game', label: 'Live game' },
  { path: '/join', label: 'Join with code' },
  { path: '/games/active', label: 'Active games' },
  { path: '/scorecard-scan', label: 'Scan scorecard' },
  { path: '/game-scorer', label: 'Hole-by-hole scorer' },
  { path: '/games/completed', label: 'Game history' },
  { path: '/tutorial', label: 'Tutorial' },
  { path: '/livsow', label: 'LivSow' },
  { path: '/chat', label: 'League chat' },
  { path: '/find-a-game', label: 'Find a game' },
];

function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth0();
  const [activeGameSession, setActiveGameSession] = useState(null);

  useEffect(() => {
    const currentGameId = localStorage.getItem('wgp_current_game');
    if (!currentGameId) return;

    const sessionKey = `wgp_session_${currentGameId}`;
    const sessionData = localStorage.getItem(sessionKey);
    if (!sessionData) return;

    try {
      const session = JSON.parse(sessionData);
      const isRecent = Date.now() - session.timestamp < 24 * 60 * 60 * 1000;
      if (isRecent && session.status !== 'completed') {
        setActiveGameSession(session);
      } else {
        localStorage.removeItem(sessionKey);
        localStorage.removeItem('wgp_current_game');
      }
    } catch (err) {
      console.error('Error parsing session data:', err);
    }
  }, []);

  return (
    <div className="wgp-home">
      <div className="wgp-home__inner">
        <header className="wgp-home__hero">
          <h1 className="wgp-home__brand">Wolf Goat Pig</h1>
          <p className="wgp-home__tagline">We accept bad golf, but not bad betting</p>
          <p className="wgp-home__place">Wing Point Golf &amp; Country Club</p>

          {!isAuthenticated ? (
            <div className="wgp-home__login">
              <p>Sign in to post for upcoming days, check standings, and record scores.</p>
              <LoginButton
                style={{
                  fontSize: '17px',
                  padding: '12px 28px',
                  background: '#047857',
                  color: 'white',
                  border: 'none',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  fontWeight: 700,
                }}
              />
            </div>
          ) : (
            <p className="wgp-home__welcome">
              Welcome back{user?.name ? `, ${user.name.split(' ')[0]}` : ''}. Pick what you need —
              the rest stays out of the way.
            </p>
          )}
        </header>

        <section className="wgp-home__pillars" aria-label="Primary actions">
          <button
            type="button"
            className="wgp-home__pillar"
            onClick={() => navigate('/signup?tab=wgp-signup')}
          >
            <span className="wgp-home__pillar-kicker">This week</span>
            <h2 className="wgp-home__pillar-title">Sign up to play</h2>
            <p className="wgp-home__pillar-copy">
              Claim an upcoming day and see who else is already on the sheet.
            </p>
          </button>

          <button
            type="button"
            className="wgp-home__pillar"
            onClick={() => navigate('/leaderboard')}
          >
            <span className="wgp-home__pillar-kicker">Standings</span>
            <h2 className="wgp-home__pillar-title">Leaderboard</h2>
            <p className="wgp-home__pillar-copy">
              Season quarters and where you sit against the field.
            </p>
          </button>

          <button
            type="button"
            className="wgp-home__pillar"
            onClick={() => navigate('/rounds/post')}
          >
            <span className="wgp-home__pillar-kicker">After the round</span>
            <h2 className="wgp-home__pillar-title">Record a score</h2>
            <p className="wgp-home__pillar-copy">
              One person posts for the group; partners attest from their accounts.
            </p>
          </button>
        </section>

        <section className="wgp-home__panel">
          <h2>How scoring works</h2>
          <p>
            You are not creating throwaway players. Pick real Wing Point profiles, post the
            group result once, and give everyone a shareable round link. Partners get notified
            to attest.
          </p>
          <ol className="wgp-home__steps">
            <li>
              <span className="wgp-home__step-num" aria-hidden="true">1</span>
              <div>
                <strong>Post for the group</strong>
                <span>
                  Stuart plays with Terry, Steve, and Brett — select their existing profiles and
                  enter the quarters result.
                </span>
              </div>
            </li>
            <li>
              <span className="wgp-home__step-num" aria-hidden="true">2</span>
              <div>
                <strong>Get a round ID</strong>
                <span>
                  Each post gets a unique round ID so the result is findable and shareable —
                  same idea as a join code for live games.
                </span>
              </div>
            </li>
            <li>
              <span className="wgp-home__step-num" aria-hidden="true">3</span>
              <div>
                <strong>Partners attest</strong>
                <span>
                  Terry, Steve, and Brett see a notification when they open the app and confirm
                  the round from earlier today.
                </span>
              </div>
            </li>
          </ol>
          <div className="wgp-home__actions">
            {isAuthenticated ? (
              <button
                type="button"
                className="wgp-home__btn wgp-home__btn--primary"
                onClick={() => navigate('/rounds/post')}
              >
                Post or attest a round
              </button>
            ) : (
              <LoginButton
                style={{
                  fontSize: '15px',
                  padding: '11px 16px',
                  background: '#047857',
                  color: 'white',
                  border: 'none',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  fontWeight: 650,
                }}
              />
            )}
            <button
              type="button"
              className="wgp-home__btn wgp-home__btn--ghost"
              onClick={() => navigate('/signup?tab=wgp-signup')}
            >
              Open this week&apos;s sign-up
            </button>
          </div>
        </section>

        <StaleGameBanner isAuthenticated={isAuthenticated} />

        {activeGameSession && (
          <div className="wgp-home__resume">
            <div>
              <strong>Active live game</strong>
              <p>
                Playing as <strong>{activeGameSession.playerName}</strong>
                {activeGameSession.joinCode ? (
                  <>
                    {' '}
                    · Join code <strong>{activeGameSession.joinCode}</strong>
                  </>
                ) : null}
              </p>
            </div>
            <button type="button" onClick={() => navigate(`/game/${activeGameSession.gameId}`)}>
              Resume
            </button>
          </div>
        )}

        <details className="wgp-home__more">
          <summary>More tools — live games, scanning, history</summary>
          <div className="wgp-home__more-grid">
            {ADVANCED_TOOLS.map((tool) => (
              <button key={tool.path} type="button" onClick={() => navigate(tool.path)}>
                {tool.label}
              </button>
            ))}
            <a
              href="https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM"
              target="_blank"
              rel="noopener noreferrer"
            >
              Legacy standings
            </a>
          </div>
        </details>

        <AuthHealthCheck />
      </div>
    </div>
  );
}

export default HomePage;
