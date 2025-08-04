import React, { useState, useEffect } from "react";
import CourseManager from "./CourseManager";

const API_URL = process.env.REACT_APP_API_URL || "";
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
  const [players, setPlayers] = useState([
    { id: 'p1', name: '', handicap: '', strength: '', is_human: true },
    { id: 'p2', name: '', handicap: '', strength: '', is_human: true },
    { id: 'p3', name: '', handicap: '', strength: '', is_human: true },
    { id: 'p4', name: '', handicap: '', strength: '', is_human: true },
  ]);
  const [courses, setCourses] = useState([]);
  const [courseName, setCourseName] = useState('');
  const [error, setError] = useState('');
  const [showCourseManager, setShowCourseManager] = useState(false);
  // GHIN lookup state
  const [ghinSearch, setGhinSearch] = useState({}); // {p1: {first_name, last_name}, ...}
  const [ghinResults, setGhinResults] = useState({}); // {p1: [], ...}
  const [ghinLoading, setGhinLoading] = useState({});
  const [ghinError, setGhinError] = useState({});

  useEffect(() => {
    fetch(`${API_URL}/courses`).then(res => res.json()).then(data => {
      setCourses(Object.keys(data));
      if (Object.keys(data).length > 0) setCourseName(Object.keys(data)[0]);
    });
  }, []);

  const handleChange = (idx, field, value) => {
    setPlayers(players => players.map((p, i) => i === idx ? { ...p, [field]: value } : p));
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
      setError(data.detail || 'Setup failed');
    }
  };

  return (
    <>
      {showCourseManager && <CourseManager onClose={() => setShowCourseManager(false)} onCoursesChanged={() => {
        fetch(`${API_URL}/courses`).then(res => res.json()).then(data => setCourses(Object.keys(data)));
      }} />}
      <form onSubmit={handleSubmit} style={{ ...cardStyle, maxWidth: 420, margin: '40px auto', background: COLORS.bg }}>
        <h2 style={{ color: COLORS.primary, marginBottom: 12 }}>Setup Players & Course</h2>
        <div style={{ marginBottom: 12, display: 'flex', flexWrap: 'wrap', gap: 8, flexDirection: window.innerWidth < 600 ? 'column' : 'row' }}>
          <label style={{ fontWeight: 600, marginRight: 8 }}>Course:</label>
          <select style={{ ...inputStyle, width: 180 }} value={courseName} onChange={e => setCourseName(e.target.value)}>
            {courses.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <button type="button" style={{ ...buttonStyle, background: COLORS.accent, marginLeft: 10, fontSize: 16, padding: "10px 18px" }} onClick={() => setShowCourseManager(true)}>Manage Courses</button>
        </div>
        {players.map((player, idx) => (
          <div key={player.id} style={{ marginBottom: 18, border: '1px solid #eee', borderRadius: 8, padding: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="text"
                placeholder="Name"
                value={player.name}
                onChange={e => handleChange(idx, 'name', e.target.value)}
                style={{ width: 120, marginRight: 8 }}
              />
              <input
                type="number"
                placeholder="Handicap"
                value={player.handicap}
                onChange={e => handleChange(idx, 'handicap', e.target.value)}
                style={{ width: 70, marginRight: 8 }}
              />
              <select
                value={player.strength}
                onChange={e => handleChange(idx, 'strength', e.target.value)}
                style={{ width: 110, marginRight: 8 }}
              >
                <option value="">Strength</option>
                <option value="Beginner">Beginner</option>
                <option value="Average">Average</option>
                <option value="Strong">Strong</option>
                <option value="Expert">Expert</option>
              </select>
              {/* GHIN Lookup UI */}
              <input type="text" placeholder="First Name (optional)" value={ghinSearch[player.id]?.first_name || ''} onChange={e => handleGhinSearchChange(player.id, 'first_name', e.target.value)} />
              <input type="text" placeholder="Last Name (required)" value={ghinSearch[player.id]?.last_name || ''} onChange={e => handleGhinSearchChange(player.id, 'last_name', e.target.value)} required />
              <button type="button" onClick={() => handleGhinLookup(player.id)} disabled={ghinLoading?.[player.id] || !ghinSearch[player.id]?.last_name} style={{ marginRight: 4 }}>
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