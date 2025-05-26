import React, { useState, useEffect } from "react";

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
  padding: "10px 18px",
  fontWeight: 600,
  fontSize: 16,
  minHeight: 44,
  margin: "8px 0",
  boxShadow: "0 1px 4px rgba(25, 118, 210, 0.08)",
  cursor: "pointer",
  transition: "background 0.2s",
};
const inputStyle = {
  border: `1px solid ${COLORS.border}`,
  borderRadius: 6,
  padding: "10px 12px",
  fontSize: 16,
  minHeight: 36,
  width: 60,
  margin: "4px 0",
};

function CourseManager({ onClose, onCoursesChanged }) {
  const [courses, setCourses] = useState([]);
  const [newName, setNewName] = useState("");
  const [newHoles, setNewHoles] = useState(Array(18).fill({ stroke_index: "", par: "", handicap: "" }));
  const [error, setError] = useState("");
  const [editIdx, setEditIdx] = useState(null);
  const [editCourse, setEditCourse] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/courses`).then(res => res.json()).then(data => setCourses(Object.entries(data)));
  }, []);

  const handleAdd = async e => {
    e.preventDefault();
    if (!newName.trim() || newHoles.some(x => !x.stroke_index || !x.par)) {
      setError("Name and all 18 holes (stroke index and par) required.");
      return;
    }
    const holes = newHoles.map(h => ({
      stroke_index: Number(h.stroke_index),
      par: Number(h.par),
      handicap: h.handicap ? Number(h.handicap) : undefined
    }));
    if (holes.some(h => isNaN(h.stroke_index) || h.stroke_index < 1 || h.stroke_index > 18 || isNaN(h.par) || h.par < 3 || h.par > 5)) {
      setError("Stroke indexes 1-18, pars 3-5.");
      return;
    }
    const res = await fetch(`${API_URL}/courses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName, holes }),
    });
    if (res.ok) {
      const data = await res.json();
      setCourses(Object.entries(data));
      setNewName("");
      setNewHoles(Array(18).fill({ stroke_index: "", par: "", handicap: "" }));
      setError("");
      onCoursesChanged && onCoursesChanged();
    } else {
      const data = await res.json();
      setError(data.detail || "Add failed");
    }
  };

  const handleDelete = async name => {
    if (!window.confirm(`Delete course '${name}'?`)) return;
    const res = await fetch(`${API_URL}/courses/${encodeURIComponent(name)}`, { method: "DELETE" });
    if (res.ok) {
      const data = await res.json();
      setCourses(Object.entries(data));
      onCoursesChanged && onCoursesChanged();
    }
  };

  const handleEdit = (idx, name, holes) => {
    setEditIdx(idx);
    setEditCourse({ name, holes: holes.map(h => ({ ...h })) });
  };

  const handleEditChange = (i, field, value) => {
    setEditCourse(ec => ({
      ...ec,
      holes: ec.holes.map((h, idx) => idx === i ? { ...h, [field]: value } : h)
    }));
  };

  const handleEditSave = async () => {
    const { name, holes } = editCourse;
    if (!name.trim() || holes.some(x => !x.stroke_index || !x.par)) {
      setError("All 18 holes (stroke index and par) required.");
      return;
    }
    const formattedHoles = holes.map(h => ({
      stroke_index: Number(h.stroke_index),
      par: Number(h.par),
      handicap: h.handicap ? Number(h.handicap) : undefined
    }));
    const res = await fetch(`${API_URL}/courses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, holes: formattedHoles }),
    });
    if (res.ok) {
      const data = await res.json();
      setCourses(Object.entries(data));
      setEditIdx(null);
      setEditCourse(null);
      setError("");
      onCoursesChanged && onCoursesChanged();
    } else {
      const data = await res.json();
      setError(data.detail || "Edit failed");
    }
  };

  return (
    <div style={{ ...cardStyle, maxWidth: 700, margin: "40px auto", background: COLORS.bg }}>
      <h2 style={{ color: COLORS.primary, marginBottom: 12 }}>Course Management</h2>
      {onClose && <button style={{ ...buttonStyle, float: "right", marginTop: -36 }} onClick={onClose}>Close</button>}
      <h3 style={{ marginTop: 0 }}>Existing Courses</h3>
      <ul style={{ paddingLeft: 18 }}>
        {courses.map(([name, holes], idx) => (
          <li key={name} style={{ marginBottom: 10 }}>
            <b>{name}</b> &nbsp;
            <span style={{ fontSize: 13, color: COLORS.muted }}>Stroke Indexes: {holes.map(h => h.stroke_index).join(", ")}</span>
            <span style={{ fontSize: 13, color: COLORS.muted, marginLeft: 8 }}>Pars: {holes.map(h => h.par).join(", ")}</span>
            {holes[0]?.handicap !== undefined && <span style={{ fontSize: 13, color: COLORS.muted, marginLeft: 8 }}>Handicaps: {holes.map(h => h.handicap ?? "-").join(", ")}</span>}
            <button style={{ ...buttonStyle, background: COLORS.error, marginLeft: 10, fontSize: 13, padding: "4px 10px" }} onClick={() => handleDelete(name)}>Delete</button>
            <button style={{ ...buttonStyle, background: COLORS.accent, marginLeft: 6, fontSize: 13, padding: "4px 10px" }} onClick={() => handleEdit(idx, name, holes)}>Edit</button>
            {editIdx === idx && editCourse && (
              <div style={{ marginTop: 10, background: COLORS.card, border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 10 }}>
                <h4>Edit {name}</h4>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {editCourse.holes.map((h, i) => (
                    <span key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", marginRight: 8 }}>
                      <input
                        style={{ ...inputStyle, width: 36, marginBottom: 2 }}
                        placeholder={`SI ${i + 1}`}
                        value={h.stroke_index}
                        onChange={e => handleEditChange(i, "stroke_index", e.target.value)}
                        maxLength={2}
                      />
                      <input
                        style={{ ...inputStyle, width: 36 }}
                        placeholder="Par"
                        value={h.par}
                        onChange={e => handleEditChange(i, "par", e.target.value)}
                        maxLength={1}
                      />
                      <input
                        style={{ ...inputStyle, width: 36 }}
                        placeholder="Hcp"
                        value={h.handicap ?? ""}
                        onChange={e => handleEditChange(i, "handicap", e.target.value)}
                        maxLength={2}
                      />
                    </span>
                  ))}
                </div>
                <button style={{ ...buttonStyle, background: COLORS.success, marginTop: 8 }} onClick={handleEditSave}>Save</button>
                <button style={{ ...buttonStyle, background: COLORS.warning, marginLeft: 8, marginTop: 8 }} onClick={() => { setEditIdx(null); setEditCourse(null); }}>Cancel</button>
              </div>
            )}
          </li>
        ))}
      </ul>
      <h3>Add New Course</h3>
      <form onSubmit={handleAdd} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <input style={{ ...inputStyle, width: 220 }} placeholder="Course Name" value={newName} onChange={e => setNewName(e.target.value)} />
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {Array(18).fill(0).map((_, i) => (
            <span key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", marginRight: 8 }}>
              <input
                style={{ ...inputStyle, width: 36, marginBottom: 2 }}
                placeholder={`SI ${i + 1}`}
                value={newHoles[i]?.stroke_index || ""}
                onChange={e => setNewHoles(newHoles.map((h, idx) => idx === i ? { ...h, stroke_index: e.target.value } : h))}
                maxLength={2}
              />
              <input
                style={{ ...inputStyle, width: 36 }}
                placeholder="Par"
                value={newHoles[i]?.par || ""}
                onChange={e => setNewHoles(newHoles.map((h, idx) => idx === i ? { ...h, par: e.target.value } : h))}
                maxLength={1}
              />
              <input
                style={{ ...inputStyle, width: 36 }}
                placeholder="Hcp"
                value={newHoles[i]?.handicap || ""}
                onChange={e => setNewHoles(newHoles.map((h, idx) => idx === i ? { ...h, handicap: e.target.value } : h))}
                maxLength={2}
              />
            </span>
          ))}
        </div>
        {error && <div style={{ color: COLORS.error }}>{error}</div>}
        <button type="submit" style={{ ...buttonStyle, width: 180 }}>Add Course</button>
      </form>
    </div>
  );
}

export default CourseManager; 