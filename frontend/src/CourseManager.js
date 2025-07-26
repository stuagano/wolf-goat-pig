import React, { useState, useEffect } from 'react';
import CourseImport from './CourseImport';

const API_URL = process.env.REACT_APP_API_URL || "";

const COLORS = {
  primary: "#2E7D32",
  secondary: "#4CAF50",
  accent: "#81C784",
  background: "#F1F8E9",
  text: "#1B5E20",
  error: "#D32F2F",
  warning: "#F57C00",
  success: "#388E3C"
};

const cardStyle = {
  background: "white",
  borderRadius: 12,
  padding: 24,
  margin: "16px 0",
  boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
  border: "1px solid #e0e0e0"
};

const buttonStyle = {
  background: COLORS.primary,
  color: "white",
  border: "none",
  borderRadius: 8,
  padding: "12px 24px",
  fontSize: 16,
  fontWeight: "bold",
  cursor: "pointer",
  margin: "8px 4px",
  transition: "background-color 0.2s"
};

function CourseManager({ onClose, onCoursesChanged }) {
  const [courses, setCourses] = useState([]);
  const [newName, setNewName] = useState("");
  const [newHoles, setNewHoles] = useState(Array(18).fill({ stroke_index: "", par: "", handicap: "" }));
  const [error, setError] = useState("");
  const [editIdx, setEditIdx] = useState(null);
  const [editCourse, setEditCourse] = useState(null);
  const [showImport, setShowImport] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await fetch(`${API_URL}/courses`);
      const data = await response.json();
      setCourses(Object.entries(data));
    } catch (error) {
      console.error("Error fetching courses:", error);
      setError("Failed to load courses");
    }
  };

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

  const handleDelete = async (courseName) => {
    if (!window.confirm(`Delete course "${courseName}"?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/courses/${encodeURIComponent(courseName)}`, {
        method: "DELETE"
      });
      
      if (response.ok) {
        await fetchCourses();
        onCoursesChanged && onCoursesChanged();
      } else {
        const data = await response.json();
        setError(data.detail || "Delete failed");
      }
    } catch (error) {
      setError("Failed to delete course");
    }
  };

  const handleEdit = (courseName) => {
    const course = courses.find(([name]) => name === courseName);
    if (course) {
      setEditCourse(course[1]);
      setEditIdx(courses.findIndex(([name]) => name === courseName));
    }
  };

  const handleSaveEdit = async () => {
    if (!editCourse) return;
    
    try {
      const response = await fetch(`${API_URL}/courses/${encodeURIComponent(editCourse.name)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editCourse)
      });
      
      if (response.ok) {
        await fetchCourses();
        setEditCourse(null);
        setEditIdx(null);
        onCoursesChanged && onCoursesChanged();
      } else {
        const data = await response.json();
        setError(data.detail || "Update failed");
      }
    } catch (error) {
      setError("Failed to update course");
    }
  };

  const handleCancelEdit = () => {
    setEditCourse(null);
    setEditIdx(null);
  };

  const handleCourseImported = (importedCourse) => {
    // Refresh the courses list
    fetchCourses();
    onCoursesChanged && onCoursesChanged();
    setShowImport(false);
  };

  return (
    <div style={{ 
      position: "fixed", 
      top: 0, 
      left: 0, 
      right: 0, 
      bottom: 0, 
      background: "rgba(0, 0, 0, 0.5)", 
      display: "flex", 
      justifyContent: "center", 
      alignItems: "center",
      zIndex: 1000
    }}>
      <div style={{ 
        background: COLORS.background, 
        borderRadius: 16, 
        padding: 24, 
        maxWidth: 1200, 
        maxHeight: "90vh", 
        overflow: "auto",
        width: "90%"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h1 style={{ color: COLORS.text, margin: 0 }}>Course Management</h1>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              fontSize: 24,
              cursor: "pointer",
              color: "#666"
            }}
          >
            ×
          </button>
        </div>

        {error && (
          <div style={{
            background: "#ffebee",
            color: COLORS.error,
            padding: 12,
            borderRadius: 8,
            marginBottom: 16,
            border: `1px solid ${COLORS.error}`
          }}>
            ❌ {error}
          </div>
        )}

        {/* Import Button */}
        <div style={{ marginBottom: 20 }}>
          <button
            onClick={() => setShowImport(true)}
            style={{
              ...buttonStyle,
              background: COLORS.secondary,
              marginRight: 12
            }}
          >
            📥 Import Course
          </button>
          <span style={{ color: "#666", fontSize: 14 }}>
            Import real course ratings and slopes from external databases
          </span>
        </div>

        {/* Add New Course Form */}
        <div style={cardStyle}>
          <h2 style={{ color: COLORS.text, marginBottom: 16 }}>Add New Course</h2>
          <form onSubmit={handleAdd}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", marginBottom: 8, fontWeight: "bold", color: COLORS.text }}>
                Course Name:
              </label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                style={{
                  width: "100%",
                  padding: "12px",
                  border: "2px solid #e0e0e0",
                  borderRadius: 8,
                  fontSize: 16
                }}
                placeholder="Enter course name"
              />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", marginBottom: 8, fontWeight: "bold", color: COLORS.text }}>
                Hole Data (18 holes):
              </label>
              <div style={{ 
                display: "grid", 
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", 
                gap: 12 
              }}>
                {newHoles.map((hole, idx) => (
                  <div key={idx} style={{ 
                    background: "#f5f5f5", 
                    padding: 12, 
                    borderRadius: 8 
                  }}>
                    <div style={{ fontWeight: "bold", marginBottom: 8 }}>Hole {idx + 1}</div>
                    <input
                      type="number"
                      placeholder="Stroke Index"
                      value={hole.stroke_index}
                      onChange={(e) => {
                        const newHolesCopy = [...newHoles];
                        newHolesCopy[idx] = { ...hole, stroke_index: e.target.value };
                        setNewHoles(newHolesCopy);
                      }}
                      style={{
                        width: "100%",
                        padding: "8px",
                        border: "1px solid #ddd",
                        borderRadius: 4,
                        marginBottom: 8
                      }}
                    />
                    <input
                      type="number"
                      placeholder="Par"
                      value={hole.par}
                      onChange={(e) => {
                        const newHolesCopy = [...newHoles];
                        newHolesCopy[idx] = { ...hole, par: e.target.value };
                        setNewHoles(newHolesCopy);
                      }}
                      style={{
                        width: "100%",
                        padding: "8px",
                        border: "1px solid #ddd",
                        borderRadius: 4
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>

            <button type="submit" style={buttonStyle}>
              Add Course
            </button>
          </form>
        </div>

        {/* Existing Courses */}
        <div style={cardStyle}>
          <h2 style={{ color: COLORS.text, marginBottom: 16 }}>Existing Courses</h2>
          {courses.length === 0 ? (
            <p style={{ color: "#666", textAlign: "center", padding: 20 }}>
              No courses found. Add a course above or import one from external sources.
            </p>
          ) : (
            <div style={{ display: "grid", gap: 16 }}>
              {courses.map(([name, course], idx) => (
                <div key={name} style={{ 
                  background: "#f5f5f5", 
                  padding: 16, 
                  borderRadius: 8,
                  border: editIdx === idx ? `2px solid ${COLORS.primary}` : "1px solid #ddd"
                }}>
                  {editIdx === idx ? (
                    <div>
                      <input
                        type="text"
                        value={editCourse.name}
                        onChange={(e) => setEditCourse({ ...editCourse, name: e.target.value })}
                        style={{
                          width: "100%",
                          padding: "8px",
                          border: "1px solid #ddd",
                          borderRadius: 4,
                          marginBottom: 8
                        }}
                      />
                      <div style={{ display: "flex", gap: 8 }}>
                        <button onClick={handleSaveEdit} style={{ ...buttonStyle, background: COLORS.success }}>
                          Save
                        </button>
                        <button onClick={handleCancelEdit} style={{ ...buttonStyle, background: "#666" }}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <h3 style={{ margin: 0, color: COLORS.text }}>{name}</h3>
                        <p style={{ margin: "4px 0", color: "#666", fontSize: 14 }}>
                          {course.holes?.length || 0} holes
                        </p>
                      </div>
                      <div style={{ display: "flex", gap: 8 }}>
                        <button onClick={() => handleEdit(name)} style={{ ...buttonStyle, background: COLORS.secondary }}>
                          Edit
                        </button>
                        <button onClick={() => handleDelete(name)} style={{ ...buttonStyle, background: COLORS.error }}>
                          Delete
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Course Import Modal */}
        {showImport && (
          <CourseImport
            onClose={() => setShowImport(false)}
            onCourseImported={handleCourseImported}
          />
        )}
      </div>
    </div>
  );
}

export default CourseManager; 