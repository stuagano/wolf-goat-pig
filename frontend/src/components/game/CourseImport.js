import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || "";

// Helper function to safely serialize error details
const formatErrorDetail = (detail) => {
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail);
  }
  return detail;
};

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

const inputStyle = {
  width: "100%",
  maxWidth: "600px",
  padding: "12px",
  border: "2px solid #e0e0e0",
  borderRadius: 8,
  fontSize: 16,
  marginBottom: 16,
  boxSizing: "border-box",
  wordBreak: "break-word",
  overflowWrap: "break-word"
};

const CourseImport = ({ onClose, onCourseImported }) => {
  const [importSources, setImportSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  const [courseName, setCourseName] = useState("");
  const [state, setState] = useState("");
  const [city, setCity] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [previewData, setPreviewData] = useState(null);

  useEffect(() => {
    fetchImportSources();
  }, []);

  const fetchImportSources = async () => {
    try {
      const response = await fetch(`${API_URL}/courses/import/sources`);
      const data = await response.json();
      setImportSources(data.sources);
    } catch (error) {
      console.error("Error fetching import sources:", error);
      setError("Failed to load import sources");
    }
  };

  const handleSourceSelect = (source) => {
    setSelectedSource(source);
    setError("");
    setSuccess("");
    setPreviewData(null);
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === "application/json") {
      setSelectedFile(file);
      setError("");
    } else {
      setError("Please select a valid JSON file");
      setSelectedFile(null);
    }
  };

  const previewCourse = async () => {
    if (!courseName.trim()) {
      setError("Please enter a course name");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(`${API_URL}/courses/import/preview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          course_name: courseName,
          state: state || undefined,
          city: city || undefined
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setPreviewData(data.course);
        setSuccess(data.message);
      } else {
        setError(formatErrorDetail(data.detail) || "Failed to preview course");
      }
    } catch (error) {
      setError("Failed to preview course");
    } finally {
      setLoading(false);
    }
  };

  const importCourse = async () => {
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      let response;

      if (selectedSource.name === "JSON File") {
        // File upload
        const formData = new FormData();
        formData.append("file", selectedFile);

        response = await fetch(`${API_URL}/courses/import/file`, {
          method: "POST",
          body: formData,
        });
      } else {
        // Search import
        response = await fetch(`${API_URL}/courses/import/search`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            course_name: courseName,
            state: state || undefined,
            city: city || undefined
          }),
        });
      }

      const data = await response.json();

      if (response.ok) {
        setSuccess(data.message);
        setPreviewData(null);
        setCourseName("");
        setState("");
        setCity("");
        setSelectedFile(null);
        
        // Notify parent component
        if (onCourseImported) {
          onCourseImported(data.course);
        }
      } else {
        setError(formatErrorDetail(data.detail) || "Failed to import course");
      }
    } catch (error) {
      setError("Failed to import course");
    } finally {
      setLoading(false);
    }
  };

  const renderSourceSelection = () => (
    <div style={cardStyle}>
      <h2 style={{ color: COLORS.text, marginBottom: 20 }}>🏌️ Import Course Data</h2>
      <p style={{ color: "#666", marginBottom: 20 }}>
        Import real course ratings and slopes from external databases or upload a JSON file.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
        {importSources.map((source) => (
          <div
            key={source.name}
            style={{
              ...cardStyle,
              border: selectedSource?.name === source.name ? `3px solid ${COLORS.primary}` : "1px solid #e0e0e0",
              cursor: "pointer",
              transition: "border-color 0.2s"
            }}
            onClick={() => handleSourceSelect(source)}
          >
            <h3 style={{ color: COLORS.text, marginBottom: 8 }}>{source.name}</h3>
            <p style={{ color: "#666", fontSize: 14, marginBottom: 12 }}>{source.description}</p>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{
                color: source.available ? COLORS.success : COLORS.error,
                fontWeight: "bold"
              }}>
                {source.available ? "✅ Available" : "❌ Not Available"}
              </span>
              {source.requires_api_key && (
                <span style={{ color: COLORS.warning, fontSize: 12 }}>🔑 API Key Required</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderSearchForm = () => (
    <div style={cardStyle}>
      <h3 style={{ color: COLORS.text, marginBottom: 16 }}>
        Search for "{selectedSource.name}" Course
      </h3>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: 16 }}>
        <div>
          <label style={{ display: "block", marginBottom: 8, fontWeight: "bold", color: COLORS.text }}>
            Course Name *
          </label>
          <input
            type="text"
            value={courseName}
            onChange={(e) => setCourseName(e.target.value)}
            placeholder="e.g., Pebble Beach Golf Links"
            style={inputStyle}
          />
        </div>

        <div>
          <label style={{ display: "block", marginBottom: 8, fontWeight: "bold", color: COLORS.text }}>
            State (Optional)
          </label>
          <input
            type="text"
            value={state}
            onChange={(e) => setState(e.target.value)}
            placeholder="e.g., CA"
            style={inputStyle}
          />
        </div>

        <div>
          <label style={{ display: "block", marginBottom: 8, fontWeight: "bold", color: COLORS.text }}>
            City (Optional)
          </label>
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="e.g., Pebble Beach"
            style={inputStyle}
          />
        </div>
      </div>

      <div style={{ display: "flex", gap: 12, marginTop: 20 }}>
        <button
          onClick={previewCourse}
          disabled={loading || !courseName.trim()}
          style={{
            ...buttonStyle,
            background: loading ? "#ccc" : COLORS.secondary
          }}
        >
          {loading ? "🔍 Searching..." : "🔍 Preview Course"}
        </button>

        <button
          onClick={() => {
            setSelectedSource(null);
            setPreviewData(null);
            setError("");
            setSuccess("");
          }}
          style={{
            ...buttonStyle,
            background: "#666"
          }}
        >
          ← Back to Sources
        </button>
      </div>
    </div>
  );

  const renderFileUpload = () => (
    <div style={cardStyle}>
      <h3 style={{ color: COLORS.text, marginBottom: 16 }}>
        Upload Course JSON File
      </h3>

      <div style={{ marginBottom: 20 }}>
        <label style={{ display: "block", marginBottom: 8, fontWeight: "bold", color: COLORS.text }}>
          Select JSON File
        </label>
        <input
          type="file"
          accept=".json"
          onChange={handleFileSelect}
          style={{ ...inputStyle, padding: "8px" }}
        />
        {selectedFile && (
          <p style={{ color: COLORS.success, marginTop: 8 }}>
            ✅ Selected: {selectedFile.name}
          </p>
        )}
      </div>

      <div style={{ 
        background: "#f5f5f5", 
        padding: 16, 
        borderRadius: 8, 
        marginBottom: 20,
        fontSize: 14,
        color: "#666"
      }}>
        <h4 style={{ marginBottom: 8, color: COLORS.text }}>JSON File Format:</h4>
        <pre style={{ fontSize: 12, overflow: "auto" }}>
{`{
  "name": "Course Name",
  "description": "Course description",
  "course_rating": 72.5,
  "slope_rating": 135,
  "holes_data": [
    {
      "hole_number": 1,
      "par": 4,
      "yards": 420,
      "handicap": 5,
      "description": "Hole description"
    }
    // ... 18 holes total
  ]
}`}
        </pre>
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        <button
          onClick={importCourse}
          disabled={loading || !selectedFile}
          style={{
            ...buttonStyle,
            background: loading ? "#ccc" : COLORS.secondary
          }}
        >
          {loading ? "📤 Uploading..." : "📤 Import Course"}
        </button>

        <button
          onClick={() => {
            setSelectedSource(null);
            setSelectedFile(null);
            setError("");
            setSuccess("");
          }}
          style={{
            ...buttonStyle,
            background: "#666"
          }}
        >
          ← Back to Sources
        </button>
      </div>
    </div>
  );

  const renderPreview = () => (
    <div style={cardStyle}>
      <h3 style={{ color: COLORS.text, marginBottom: 16 }}>
        Course Preview
      </h3>

      {previewData && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16, marginBottom: 20 }}>
            <div>
              <strong>Name:</strong> {previewData.name}
            </div>
            <div>
              <strong>Source:</strong> {previewData.source}
            </div>
            <div>
              <strong>Total Par:</strong> {previewData.total_par}
            </div>
            <div>
              <strong>Total Yards:</strong> {previewData.total_yards.toLocaleString()}
            </div>
            <div>
              <strong>Course Rating:</strong> {previewData.course_rating || "N/A"}
            </div>
            <div>
              <strong>Slope Rating:</strong> {previewData.slope_rating || "N/A"}
            </div>
          </div>

          {previewData.description && (
            <div style={{ marginBottom: 16 }}>
              <strong>Description:</strong> {previewData.description}
            </div>
          )}

          <div style={{ marginBottom: 20 }}>
            <strong>Holes Preview:</strong>
            <div style={{ 
              display: "grid", 
              gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", 
              gap: 8,
              marginTop: 8,
              maxHeight: 200,
              overflow: "auto"
            }}>
              {previewData.holes.slice(0, 6).map((hole) => (
                <div key={hole.hole_number} style={{ 
                  background: "#f5f5f5", 
                  padding: 8, 
                  borderRadius: 4,
                  fontSize: 12
                }}>
                  <strong>Hole {hole.hole_number}:</strong> Par {hole.par}, {hole.yards} yards
                </div>
              ))}
              {previewData.holes.length > 6 && (
                <div style={{ 
                  background: "#f5f5f5", 
                  padding: 8, 
                  borderRadius: 4,
                  fontSize: 12,
                  textAlign: "center"
                }}>
                  ... and {previewData.holes.length - 6} more holes
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 12 }}>
        <button
          onClick={importCourse}
          disabled={loading}
          style={{
            ...buttonStyle,
            background: loading ? "#ccc" : COLORS.success
          }}
        >
          {loading ? "📥 Importing..." : "📥 Import Course"}
        </button>

        <button
          onClick={() => {
            setPreviewData(null);
            setSuccess("");
          }}
          style={{
            ...buttonStyle,
            background: "#666"
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );

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
        maxWidth: 800,
        maxHeight: "90vh",
        overflowY: "auto",
        overflowX: "hidden",
        width: "90%",
        boxSizing: "border-box"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h1 style={{ color: COLORS.text, margin: 0 }}>Import Course Data</h1>
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

        {success && (
          <div style={{
            background: "#e8f5e8",
            color: COLORS.success,
            padding: 12,
            borderRadius: 8,
            marginBottom: 16,
            border: `1px solid ${COLORS.success}`
          }}>
            ✅ {success}
          </div>
        )}

        {!selectedSource && renderSourceSelection()}
        {selectedSource && selectedSource.name !== "JSON File" && renderSearchForm()}
        {selectedSource && selectedSource.name === "JSON File" && renderFileUpload()}
        {previewData && renderPreview()}
      </div>
    </div>
  );
};

export default CourseImport; 