// frontend/src/components/game/scorecardParts/ScorecardEditHoleModal.jsx
// Modal for correcting a player's strokes/quarters on a hole from the Scorecard.
import React from 'react';
import PropTypes from 'prop-types';
import { Card, Button, Input } from '../../ui';
import { useTheme } from '../../../theme/Provider';
import { getHoleInfo } from './scorecardUtils';

const BettingActions = ({ holeData }) => {
  const theme = useTheme();
  const narrative = holeData?.betting_narrative;
  const wager = holeData?.wager;
  if (!(narrative || (wager && wager > 2))) return null;

  return (
    <div style={{
      marginBottom: '16px',
      padding: '12px',
      backgroundColor: 'rgba(255, 152, 0, 0.1)',
      borderRadius: '8px',
      border: '1px solid rgba(255, 152, 0, 0.3)'
    }}>
      <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#F57C00', marginBottom: '4px' }}>
        Betting Actions
      </div>
      {narrative && (
        <div style={{ fontSize: '13px', color: theme.colors.textPrimary }}>
          {narrative}
        </div>
      )}
      {wager && (
        <div style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '4px' }}>
          Final Wager: {wager}Q
        </div>
      )}
    </div>
  );
};

BettingActions.propTypes = {
  holeData: PropTypes.object
};

const ScorecardEditHoleModal = ({ players, holeHistory, editing }) => {
  const theme = useTheme();
  const {
    editingHole,
    editingPlayer,
    editStrokes,
    setEditStrokes,
    editQuarters,
    setEditQuarters,
    savingEdit,
    editSaveError,
    syncFeedback,
    handleCancelEdit,
    handleSaveEdit
  } = editing;

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
      zIndex: 1000
    }}>
      <Card style={{
        maxWidth: '400px',
        width: '90%',
        padding: '24px'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '16px' }}>
          Edit Hole {editingHole} - {(Array.isArray(players) && players.find(p => p && p.id === editingPlayer)?.name) || 'Unknown'}
        </h3>

        {/* Betting Narrative Display (read-only) */}
        <BettingActions holeData={getHoleInfo(holeHistory, editingHole)} />

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Strokes (Gross Score):
          </label>
          <Input
            type="number"
            value={editStrokes}
            disabled={savingEdit}
            onChange={(e) => setEditStrokes(e.target.value)}
            min="0"
            max="15"
            variant="inline"
            inputStyle={{
              width: '100%',
              padding: '8px',
              fontSize: '16px',
              border: `1px solid ${theme.colors.border}`,
              borderRadius: '4px'
            }}
          />
          <p style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '4px' }}>
            Actual number of strokes taken on this hole
          </p>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Quarters (Manual Override):
          </label>
          <Input
            type="number"
            value={editQuarters}
            disabled={savingEdit}
            onChange={(e) => setEditQuarters(e.target.value)}
            min="-10"
            max="10"
            step="0.5"
            variant="inline"
            inputStyle={{
              width: '100%',
              padding: '8px',
              fontSize: '16px',
              border: `2px solid ${theme.colors.warning || '#ff9800'}`,
              borderRadius: '4px',
              backgroundColor: 'rgba(255, 152, 0, 0.05)'
            }}
          />
          <p style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '4px' }}>
            ⚠️ Override automatic quarter calculation. Use when scores are correct but quarters are wrong.
            <br />
            Positive for winning (+), negative for losing (-)
          </p>
        </div>

        {(editSaveError || syncFeedback.error) && <p role="alert" style={{ color: '#b91c1c' }}>{editSaveError || syncFeedback.error} Your edits are still here. You can retry saving.</p>}
        {syncFeedback.message && <p role="status">{syncFeedback.message}</p>}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <Button variant="secondary" onClick={handleCancelEdit} disabled={savingEdit}>
            {syncFeedback.submitted ? 'Close' : 'Cancel'}
          </Button>
          <Button variant="primary" onClick={handleSaveEdit} disabled={savingEdit}>
            {savingEdit ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </Card>
    </div>
  );
};

ScorecardEditHoleModal.propTypes = {
  players: PropTypes.array,
  holeHistory: PropTypes.array,
  editing: PropTypes.object.isRequired
};

export default ScorecardEditHoleModal;
