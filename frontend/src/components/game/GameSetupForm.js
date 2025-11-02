import React, { useState, useEffect } from "react";
import CourseManager from "./CourseManager";
import PlayerProfileManager from "../PlayerProfileManager";
// import usePlayerProfile from "../../hooks/usePlayerProfile"; // Temporarily disabled

const API_URL = process.env.REACT_APP_API_URL || "";

// Helper function to safely serialize error details
const formatErrorDetail = (detail) => {
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail);
  }
  return detail;
};
const COLORS = {
  primary: "#1976d2",
  accent: "#00bcd4",
  warning: "#ff9800",
  error: "#d32f2f",
  success: "#388e3c",
  bg: "#f9fafe",
  card: "#fff",
  border: "#e0e0e0",
  text: "#222",
  muted: "#888",
};
const cardStyle = {
  background: COLORS.card,
  borderRadius: 12,
  boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
  padding: 16,
  marginBottom: 18,
  border: `1px solid ${COLORS.border}`,
};
const buttonStyle = {
  background: COLORS.primary,
  color: "#fff",
  border: "none",
  borderRadius: 8,
  padding: "14px 24px",
  fontWeight: 600,
  fontSize: 18,
  minHeight: 44,
  margin: "8px 0",
  boxShadow: "0 1px 4px rgba(25, 118, 210, 0.08)",
  cursor: "pointer",
  transition: "background 0.2s",
};
const inputStyle = {
  border: `1px solid ${COLORS.border}`,
  borderRadius: 6,
  padding: "12px 16px",
  fontSize: 18,
  minHeight: 44,
  width: 60,
  margin: "4px 0",
};

function GameSetupForm({ onSetup }) {
  // TODO: Re-enable profile management once backend API is ready
  // TODO: Restore usePlayerProfile hook when profile system is fully implemented
  // Temporarily simplified profile handling - these stubs replace the full profile system
  const selectedProfile = null;
  const profiles = [];
  const hasProfiles = false;
  const selectProfile = () => {};

  const [players, setPlayers] = useState([
    { id: 'p1', name: '', handicap: '', strength: '', is_human: true, profile_id: null },
    { id: 'p2', name: '', handicap: '', strength: '', is_human: true, profile_id: null },
    { id: 'p3', name: '', handicap: '', strength: '', is_human: true, profile_id: null },
    { id: 'p4', name: '', handicap: '', strength: '', is_human: true, profile_id: null },
  ]);
  const [courses, setCourses] = useState([]);
  const [courseName, setCourseName] = useState('');
  const [error, setError] = useState('');
  const [showCourseManager, setShowCourseManager] = useState(false);
  const [showProfileManager, setShowProfileManager] = useState(false);
  const [setupMode, setSetupMode] = useState('quick'); // 'quick' or 'profile'
  // GHIN lookup state
  const [ghinSearch, setGhinSearch] = useState({}); // {p1: {first_name, last_name}, ...}
  const [ghinResults, setGhinResults] = useState({}); // {p1: [], ...}
  const [ghinLoading, setGhinLoading] = useState({});
  const [ghinError, setGhinError] = useState({});

  useEffect(() => {
    fetch(`${API_URL}/courses`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        if (!data || typeof data !== 'object') {
          throw new Error('Invalid courses data format');
        }
        
        const courseNames = Object.keys(data);
        setCourses(courseNames);
        
        if (courseNames.length > 0) {
          setCourseName(courseNames[0]);
        } else {
          throw new Error('No courses available');
        }
      })
      .catch(error => {
        console.error('Failed to load courses:', error);
        
        // Provide fallback courses so game can still start
        const fallbackCourses = ["Default Course"];
        setCourses(fallbackCourses);
        setCourseName("Default Course");
        
        // Set error to show user-friendly message
        setError('Unable to load courses from server. Using default course. The game can still be played.');
        
        // Clear error after 5 seconds to not permanently block the UI
        setTimeout(() => {
          setError('');
        }, 5000);
      });
  }, []);

  // Auto-populate first player with selected profile
  useEffect(() => {
    if (selectedProfile && setupMode === 'profile') {
      setPlayers(prevPlayers => prevPlayers.map((p, i) => 
        i === 0 ? {
          ...p,
          name: selectedProfile.name,
          handicap: selectedProfile.handicap.toString(),
          strength: getStrengthFromHandicap(selectedProfile.handicap),
          profile_id: selectedProfile.id
        } : p
      ));
    }
  }, [selectedProfile, setupMode]);

  const getStrengthFromHandicap = (handicap) => {
    const h = parseFloat(handicap);
    if (h <= 5) return 'Expert';
    if (h <= 10) return 'Strong';
    if (h <= 15) return 'Average';
    return 'Beginner';
  };

  const handleChange = (idx, field, value) => {
    setPlayers(players => players.map((p, i) => i === idx ? { ...p, [field]: value } : p));
  };

  const handleProfileSelect = (idx, profile) => {
    if (profile) {
      setPlayers(prevPlayers => prevPlayers.map((p, i) => 
        i === idx ? {
          ...p,
          name: profile.name,
          handicap: profile.handicap.toString(),
          strength: getStrengthFromHandicap(profile.handicap),
          profile_id: profile.id
        } : p
      ));
    } else {
      setPlayers(prevPlayers => prevPlayers.map((p, i) => 
        i === idx ? {
          ...p,
          name: '',
          handicap: '',
          strength: '',
          profile_id: null
        } : p
      ));
    }
  };

  // GHIN lookup handlers
  const handleGhinSearchChange = (pid, field, value) => {
    setGhinSearch(s => ({ ...s, [pid]: { ...s[pid], [field]: value } }));
  };
  const handleGhinLookup = async (pid) => {
    const search = ghinSearch[pid] || {};
    if (!search.last_name || !search.last_name.trim()) return;
    setGhinLoading(l => ({ ...l, [pid]: true }));
    setGhinError(e => ({ ...e, [pid]: '' }));
    setGhinResults(r => ({ ...r, [pid]: [] }));
    try {
      const params = new URLSearchParams({
        last_name: search.last_name,
        ...(search.first_name ? { first_name: search.first_name } : {})
      });
      const res = await fetch(`${API_URL}/ghin/lookup?${params.toString()}`);
      if (!res.ok) throw new Error('Lookup failed');
      const data = await res.json();
      setGhinResults(r => ({ ...r, [pid]: data }));
    } catch (err) {
      setGhinError(e => ({ ...e, [pid]: err.message }));
    } finally {
      setGhinLoading(l => ({ ...l, [pid]: false }));
    }
  };
  const handleGhinSelect = (pid, golfer) => {
    setPlayers(players => players.map(p => p.id === pid ? {
      ...p,
      name: golfer.name,
      handicap: golfer.handicap || '',
      is_human: true  // All players in GameSetupForm are human
    } : p));
    setGhinResults(r => ({ ...r, [pid]: [] }));
    setGhinSearch(s => ({ ...s, [pid]: '' }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    if (players.some(p => !p.name || p.handicap === '' || !p.strength)) {
      setError('All names, handicaps, and strengths are required.');
      return;
    }
    setError('');
    const res = await fetch(`${API_URL}/game/setup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ players, course_name: courseName }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      onSetup(data.game_state);
    } else {
      setError(formatErrorDetail(data.detail) || 'Setup failed');
    }
  };

  return (
    <>
      {showCourseManager && <CourseManager onClose={() => setShowCourseManager(false)} onCoursesChanged={() => {
        fetch(`${API_URL}/courses`)
          .then(res => {
            if (!res.ok) {
              throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            return res.json();
          })
          .then(data => {
            if (data && typeof data === 'object') {
              setCourses(Object.keys(data));
            }
          })
          .catch(error => {
            console.error('Failed to refresh courses:', error);
            setError('Failed to refresh courses from server.');
            setTimeout(() => setError(''), 3000);
          });
      }} />}
      {showProfileManager && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ backgroundColor: 'white', borderRadius: 12, maxWidth: '90vw', maxHeight: '90vh', overflowY: 'auto', overflowX: 'hidden', padding: 20, boxSizing: 'border-box' }}>
            <PlayerProfileManager 
              onProfileSelect={(profile) => {
                selectProfile(profile);
                setShowProfileManager(false);
              }}
              selectedProfile={selectedProfile}
              showSelector={false}
            />
            <button 
              onClick={() => setShowProfileManager(false)}
              style={{ ...buttonStyle, background: COLORS.muted, marginTop: 16 }}
            >
              Close
            </button>
          </div>
        </div>
      )}
      <form onSubmit={handleSubmit} style={{ ...cardStyle, maxWidth: 480, margin: '40px auto', background: COLORS.bg }}>
        <h2 style={{ color: COLORS.primary, marginBottom: 12 }}>Setup Players & Course</h2>
        
        {/* Setup Mode Toggle */}
        <div style={{ marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
          <label style={{ fontWeight: 600 }}>Setup Mode:</label>
          <button
            type="button"
            onClick={() => setSetupMode('quick')}
            style={{
              ...buttonStyle,
              padding: '8px 16px',
              fontSize: 14,
              background: setupMode === 'quick' ? COLORS.primary : COLORS.muted
            }}
          >
            Quick Setup
          </button>
          <button
            type="button"
            onClick={() => setSetupMode('profile')}
            style={{
              ...buttonStyle,
              padding: '8px 16px',
              fontSize: 14,
              background: setupMode === 'profile' ? COLORS.primary : COLORS.muted
            }}
          >
            Use Profiles
          </button>
          <button
            type="button"
            onClick={() => setShowProfileManager(true)}
            style={{
              ...buttonStyle,
              padding: '8px 16px',
              fontSize: 14,
              background: COLORS.accent
            }}
          >
            Manage Profiles
          </button>
        </div>

        {/* Profile Selection for Profile Mode */}
        {setupMode === 'profile' && (
          <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f8f9fa', borderRadius: 8, border: '1px solid #e9ecef' }}>
            <h4 style={{ margin: '0 0 8px 0', color: COLORS.primary }}>Your Profile</h4>
            {selectedProfile ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <strong>{selectedProfile.name}</strong> (Handicap: {selectedProfile.handicap})
                </div>
                <button
                  type="button"
                  onClick={() => selectProfile(null)}
                  style={{ ...buttonStyle, padding: '4px 8px', fontSize: 12, background: COLORS.warning }}
                >
                  Change
                </button>
              </div>
            ) : (
              <div>
                <p style={{ margin: '0 0 8px 0', color: COLORS.muted }}>No profile selected</p>
                {hasProfiles ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {profiles.slice(0, 3).map(profile => (
                      <button
                        key={profile.id}
                        type="button"
                        onClick={() => selectProfile(profile)}
                        style={{ ...buttonStyle, padding: '6px 12px', fontSize: 12, background: COLORS.accent }}
                      >
                        {profile.name}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p style={{ margin: 0, color: COLORS.muted, fontSize: 14 }}>
                    Create a profile to track your statistics across games.
                  </p>
                )}
              </div>
            )}
          </div>
        )}
        <div style={{ marginBottom: 12, display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
          <label style={{ fontWeight: 600, flexShrink: 0 }}>Course:</label>
          <select style={{ ...inputStyle, width: 180, minWidth: 120, maxWidth: 250, boxSizing: 'border-box', flex: '1 1 auto' }} value={courseName} onChange={e => setCourseName(e.target.value)}>
            {courses.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <button type="button" style={{ ...buttonStyle, background: COLORS.accent, fontSize: 16, padding: "10px 18px", whiteSpace: 'nowrap' }} onClick={() => setShowCourseManager(true)}>Manage Courses</button>
        </div>
        {players.map((player, idx) => (
          <div key={player.id} style={{ marginBottom: 18, border: '1px solid #eee', borderRadius: 8, padding: 12 }}>
            {/* Profile Selection for Profile Mode */}
            {setupMode === 'profile' && idx > 0 && (
              <div style={{ marginBottom: 12 }}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
                  Player {idx + 1} Profile (Optional):
                </label>
                <select
                  value={player.profile_id || ''}
                  onChange={e => {
                    const profileId = e.target.value;
                    const selectedProfile = profiles.find(p => p.id === parseInt(profileId));
                    handleProfileSelect(idx, selectedProfile);
                  }}
                  style={{ width: '100%', maxWidth: '400px', marginBottom: 8, boxSizing: 'border-box' }}
                >
                  <option value="">Manual Entry</option>
                  {profiles.map(profile => (
                    <option key={profile.id} value={profile.id}>
                      {profile.name} (Handicap: {profile.handicap})
                    </option>
                  ))}
                </select>
              </div>
            )}
            
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <label htmlFor={`player-${idx}-name`} style={{ fontSize: 12, fontWeight: 600 }}>
                Player {idx + 1} Name
              </label>
              <input
                type="text"
                placeholder="Name"
                value={player.name}
                onChange={e => handleChange(idx, 'name', e.target.value)}
                style={{ width: 120, minWidth: 80, maxWidth: 200, marginRight: 8, boxSizing: 'border-box', flex: '1 1 auto' }}
                id={`player-${idx}-name`}
                disabled={setupMode === 'profile' && idx === 0 && selectedProfile}
              />
              <label htmlFor={`player-${idx}-handicap`} style={{ fontSize: 12, fontWeight: 600, flexShrink: 0 }}>
                Handicap
              </label>
              <input
                type="number"
                placeholder="Handicap"
                value={player.handicap}
                onChange={e => handleChange(idx, 'handicap', e.target.value)}
                style={{ width: 70, minWidth: 60, maxWidth: 100, marginRight: 8, boxSizing: 'border-box', flex: '0 1 auto' }}
                id={`player-${idx}-handicap`}
                disabled={setupMode === 'profile' && idx === 0 && selectedProfile}
              />
              <select
                value={player.strength}
                onChange={e => handleChange(idx, 'strength', e.target.value)}
                style={{ width: 110, minWidth: 90, maxWidth: 150, marginRight: 8, boxSizing: 'border-box', flex: '0 1 auto' }}
                disabled={setupMode === 'profile' && ((idx === 0 && selectedProfile) || player.profile_id)}
              >
                <option value="">Strength</option>
                <option value="Beginner">Beginner</option>
                <option value="Average">Average</option>
                <option value="Strong">Strong</option>
                <option value="Expert">Expert</option>
              </select>
              
              {/* Profile indicator */}
              {player.profile_id && (
                <span style={{ fontSize: 12, color: COLORS.success, fontWeight: 600 }}>
                  📊 Profile
                </span>
              )}
              {/* GHIN Lookup UI */}
              <input
                type="text"
                placeholder="First Name (optional)"
                value={ghinSearch[player.id]?.first_name || ''}
                onChange={e => handleGhinSearchChange(player.id, 'first_name', e.target.value)}
                style={{ width: 120, minWidth: 80, maxWidth: 180, padding: 6, marginRight: 4, boxSizing: 'border-box', borderRadius: 4, border: '1px solid #ccc' }}
              />
              <input
                type="text"
                placeholder="Last Name (required)"
                value={ghinSearch[player.id]?.last_name || ''}
                onChange={e => handleGhinSearchChange(player.id, 'last_name', e.target.value)}
                required
                style={{ width: 120, minWidth: 80, maxWidth: 180, padding: 6, marginRight: 4, boxSizing: 'border-box', borderRadius: 4, border: '1px solid #ccc' }}
              />
              <button
                type="button"
                onClick={() => handleGhinLookup(player.id)}
                disabled={ghinLoading?.[player.id] || !ghinSearch[player.id]?.last_name}
                style={{ marginRight: 4, padding: '6px 12px', borderRadius: 4, border: '1px solid #ccc', background: '#f5f5f5', cursor: 'pointer', whiteSpace: 'nowrap' }}
              >
                {ghinLoading?.[player.id] ? 'Searching...' : 'GHIN Lookup'}
              </button>
            </div>
            {ghinError?.[player.id] && <div style={{ color: 'red', fontSize: 13 }}>{ghinError[player.id]}</div>}
            {ghinResults?.[player.id]?.length > 0 && (
              <div style={{ marginTop: 6, background: '#f9f9f9', border: '1px solid #ddd', borderRadius: 6, padding: 8 }}>
                <div style={{ fontSize: 13, marginBottom: 4 }}>Select a golfer:</div>
                {ghinResults[player.id].map(golfer => (
                  <div key={golfer.ghin} style={{ padding: 4, cursor: 'pointer', borderBottom: '1px solid #eee' }} onClick={() => handleGhinSelect(player.id, golfer)}>
                    <strong>{golfer.name}</strong> (GHIN: {golfer.ghin})<br />
                    Club: {golfer.club} | Handicap: {golfer.handicap ?? 'N/A'}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {error && <div style={{ color: COLORS.error, marginBottom: 8 }}>{error}</div>}
        <button type="submit" style={{ ...buttonStyle, width: '100%' }}>Start Game</button>
      </form>
    </>
  );
}

export default GameSetupForm; 
