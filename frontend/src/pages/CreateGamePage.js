import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../theme/Provider';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || "";

function CreateGamePage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth0();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [courses, setCourses] = useState([]);
  const [courseName, setCourseName] = useState('');
  const [playerCount, setPlayerCount] = useState(4);

  useEffect(() => {
    // Fetch available courses
    fetch(`${API_URL}/courses`)
      .then(res => res.json())
      .then(data => {
        const courseNames = Object.keys(data);
        setCourses(courseNames);
        if (courseNames.length > 0) {
          setCourseName(courseNames[0]);
        }
      })
      .catch(error => {
        console.error('Failed to load courses:', error);
        setCourses(['Wing Point Golf & Country Club']);
        setCourseName('Wing Point Golf & Country Club');
      });
  }, []);

  const createGame = async () => {
    setLoading(true);
    setError('');

    try {
      const params = new URLSearchParams({
        course_name: courseName,
        player_count: playerCount.toString()
      });

      // Include user_id if authenticated
      if (isAuthenticated && user?.sub) {
        params.append('user_id', user.sub);
      }

      const response = await fetch(`${API_URL}/games/create?${params.toString()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error('Failed to create game');
      }

      const data = await response.json();

      // Navigate to lobby with the game ID
      navigate(`/lobby/${data.game_id}`);

    } catch (err) {
      console.error('Error creating game:', err);
      setError('Failed to create game. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      maxWidth: 600,
      margin: '0 auto',
      padding: 20,
      fontFamily: theme.typography.fontFamily
    }}>
      <div style={theme.cardStyle}>
        <h1 style={{ color: theme.colors.primary, marginBottom: 8 }}>
          🎮 Create New Game
        </h1>
        <p style={{ color: theme.colors.textSecondary, marginBottom: 24 }}>
          Set up a game and share the join code with your friends!
        </p>

        {/* Course Selection */}
        <div style={{ marginBottom: 20 }}>
          <label style={{
            display: 'block',
            fontWeight: 600,
            marginBottom: 8,
            color: theme.colors.textPrimary
          }}>
            Course:
          </label>
          <select
            value={courseName}
            onChange={(e) => setCourseName(e.target.value)}
            style={{
              width: '100%',
              padding: 12,
              fontSize: 16,
              borderRadius: 8,
              border: `1px solid ${theme.colors.border}`,
              background: theme.colors.paper
            }}
          >
            {courses.map(course => (
              <option key={course} value={course}>{course}</option>
            ))}
          </select>
        </div>

        {/* Player Count */}
        <div style={{ marginBottom: 20 }}>
          <label style={{
            display: 'block',
            fontWeight: 600,
            marginBottom: 8,
            color: theme.colors.textPrimary
          }}>
            Number of Players:
          </label>
          <select
            value={playerCount}
            onChange={(e) => setPlayerCount(parseInt(e.target.value))}
            style={{
              width: '100%',
              padding: 12,
              fontSize: 16,
              borderRadius: 8,
              border: `1px solid ${theme.colors.border}`,
              background: theme.colors.paper
            }}
          >
            <option value={2}>2 Players</option>
            <option value={3}>3 Players</option>
            <option value={4}>4 Players (Standard)</option>
            <option value={5}>5 Players</option>
            <option value={6}>6 Players</option>
          </select>
        </div>

        {/* Info Box */}
        <div style={{
          background: '#e3f2fd',
          border: `1px solid ${theme.colors.primary}`,
          borderRadius: 8,
          padding: 16,
          marginBottom: 24
        }}>
          <p style={{ margin: 0, fontSize: 14, color: theme.colors.textPrimary }}>
            <strong>How it works:</strong>
          </p>
          <ol style={{ margin: '8px 0 0 0', paddingLeft: 20, fontSize: 14 }}>
            <li>Create the game to get a join code</li>
            <li>Share the code with your friends</li>
            <li>They visit this site and enter the code</li>
            <li>Start the game when everyone has joined!</li>
          </ol>
        </div>

        {error && (
          <div style={{
            background: '#ffebee',
            color: theme.colors.error,
            padding: 12,
            borderRadius: 8,
            marginBottom: 16
          }}>
            {error}
          </div>
        )}

        {/* Create Button */}
        <button
          onClick={createGame}
          disabled={loading}
          style={{
            ...theme.buttonStyle,
            width: '100%',
            fontSize: 18,
            padding: '16px 24px',
            background: loading ? theme.colors.textSecondary : theme.colors.primary,
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Creating Game...' : '🚀 Create Game & Get Join Code'}
        </button>

        {/* Back Button */}
        <button
          onClick={() => navigate('/')}
          style={{
            ...theme.buttonStyle,
            width: '100%',
            fontSize: 16,
            marginTop: 12,
            background: 'transparent',
            color: theme.colors.textSecondary,
            border: `1px solid ${theme.colors.border}`
          }}
        >
          ← Back to Home
        </button>
      </div>
    </div>
  );
}

export default CreateGamePage;
