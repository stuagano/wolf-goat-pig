import React from "react";
import PropTypes from "prop-types";
import { Input } from "../ui";

/**
 * Modal for editing a player's name
 */
const EditPlayerNameModal = ({
  value,
  onChange,
  onSave,
  onCancel,
  theme,
}) => {
  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1001,
        padding: "20px",
      }}
    >
      <div
        style={{
          background: "white",
          padding: "24px",
          borderRadius: "12px",
          maxWidth: "400px",
          width: "100%",
          boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
        }}
      >
        <h3
          style={{
            marginTop: 0,
            marginBottom: "16px",
            color: theme.colors.primary,
          }}
        >
          Edit Player Name
        </h3>

        <div style={{ marginBottom: "24px" }}>
          <label
            style={{
              display: "block",
              marginBottom: "8px",
              fontWeight: "bold",
              color: theme.colors.textPrimary,
            }}
          >
            Player Name:
          </label>
          <Input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Enter player name"
            maxLength="50"
            autoFocus
            variant="inline"
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                onSave();
              }
            }}
            inputStyle={{
              width: "100%",
              padding: "12px",
              fontSize: "16px",
              border: `2px solid ${theme.colors.border}`,
              borderRadius: "8px",
              outline: "none",
              transition: "border-color 0.2s",
              boxSizing: "border-box",
            }}
            onFocus={(e) => (e.target.style.borderColor = theme.colors.primary)}
            onBlur={(e) => (e.target.style.borderColor = theme.colors.border)}
          />
          <p
            style={{
              fontSize: "12px",
              color: theme.colors.textSecondary,
              marginTop: "8px",
              marginBottom: 0,
            }}
          >
            Press Enter to save, or click Save button
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: "12px",
            justifyContent: "flex-end",
          }}
        >
          <button
            onClick={onCancel}
            style={{
              padding: "10px 20px",
              fontSize: "16px",
              fontWeight: "bold",
              border: `2px solid ${theme.colors.border}`,
              borderRadius: "8px",
              background: "white",
              color: theme.colors.textPrimary,
              cursor: "pointer",
            }}
          >
            Cancel
          </button>
          <button
            onClick={onSave}
            style={{
              padding: "10px 20px",
              fontSize: "16px",
              fontWeight: "bold",
              border: "none",
              borderRadius: "8px",
              background: theme.colors.primary,
              color: "white",
              cursor: "pointer",
            }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

EditPlayerNameModal.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  theme: PropTypes.shape({
    colors: PropTypes.shape({
      primary: PropTypes.string,
      border: PropTypes.string,
      textPrimary: PropTypes.string,
      textSecondary: PropTypes.string,
    }),
  }).isRequired,
};

export default EditPlayerNameModal;
