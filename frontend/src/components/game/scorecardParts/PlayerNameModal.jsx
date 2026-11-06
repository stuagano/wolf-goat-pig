// frontend/src/components/game/scorecardParts/PlayerNameModal.jsx
// Modal for renaming a player from the Scorecard (simulation mode only).
import React from 'react';
import PropTypes from 'prop-types';
import { Card, Button, Input } from '../../ui';
import { useTheme } from '../../../theme/Provider';

const PlayerNameModal = ({ value, onChange, onSave, onCancel }) => {
  const theme = useTheme();

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1001
    }}>
      <Card style={{
        maxWidth: '400px',
        width: '90%',
        padding: '24px'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '16px' }}>
          Edit Player Name
        </h3>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
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
              if (e.key === 'Enter') {
                onSave();
              }
            }}
            inputStyle={{
              width: '100%',
              padding: '12px',
              fontSize: '16px',
              border: `1px solid ${theme.colors.border}`,
              borderRadius: '4px'
            }}
          />
          <p style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '4px' }}>
            Press Enter to save, or click Save button
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="primary" onClick={onSave}>
            Save
          </Button>
        </div>
      </Card>
    </div>
  );
};

PlayerNameModal.propTypes = {
  value: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired
};

export default PlayerNameModal;
