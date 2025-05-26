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
    { id: 'p1', name: '', handicap: '', strength: '' },
    { id: 'p2', name: '', handicap: '', strength: '' },
    { id: 'p3', name: '', handicap: '', strength: '' },
    { id: 'p4', name: '', handicap: '', strength: '' },
  ]);
  const [courses, setCourses] = useState([]);
  const [courseName, setCourseName] = useState('');
  const [error, setError] = useState('');
  const [showCourseManager, setShowCourseManager] = useState(false);
  useEffect(() => {
    fetch(`${API_URL}/courses`).then(res => res.json()).then(data => {
      setCourses(Object.keys(data));
      if (Object.keys(data).length > 0) setCourseName(Object.keys(data)[0]);
    });
  }, []);
  const handleChange = (idx, field, value) => {
    setPlayers(players => players.map((p, i) => i === idx ? { ...p, [field]: value } : p));
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
        {players.map((p, i) => (
          <div key={p.id} style={{ display: 'flex', gap: 8, marginBottom: 8, flexDirection: window.innerWidth < 600 ? 'column' : 'row' }}>
            <input
              style={{ ...inputStyle, flex: 2 }}
              placeholder={`Player ${i + 1} Name`}
              value={p.name}
              onChange={e => handleChange(i, 'name', e.target.value)}
              required
            />
            <input
              style={{ ...inputStyle, flex: 1 }}
              placeholder="Handicap"
              type="number"
              min="0"
              step="0.5"
              value={p.handicap}
              onChange={e => handleChange(i, 'handicap', e.target.value)}
              required
            />
            <select
              style={{ ...inputStyle, flex: 1 }}
              value={p.strength || ''}
              onChange={e => handleChange(i, 'strength', e.target.value)}
              required
            >
              <option value="">Strength</option>
              <option value="Beginner">Beginner</option>
              <option value="Average">Average</option>
              <option value="Strong">Strong</option>
              <option value="Expert">Expert</option>
            </select>
          </div>
        ))}
        {error && <div style={{ color: COLORS.error, marginBottom: 8 }}>{error}</div>}
        <button type="submit" style={{ ...buttonStyle, width: '100%' }}>Start Game</button>
      </form>
    </>
  );
}

export default GameSetupForm; 