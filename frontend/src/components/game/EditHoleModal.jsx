/**
 * EditHoleModal - Modal for editing scores and quarters of a completed hole.
 *
 * Shows all players' strokes and quarters for a single hole. Saves directly
 * to holeHistory without overwriting the current hole being scored.
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';

const EditHoleModal = ({
  isOpen,
  onClose,
  onSave,
  holeData,
  players,
}) => {
  const theme = useTheme();
  const [scores, setScores] = useState({});
  const [quarters, setQuarters] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen && holeData) {
      setScores({ ...holeData.gross_scores });
      setQuarters(
        Object.fromEntries(
          players.map(p => [p.id, (holeData.points_delta?.[p.id] ?? 0).toString()])
        )
      );
    }
  }, [isOpen, holeData, players]);

  const handleSave = useCallback(async () => {
    const parsedQuarters = {};
    for (const p of players) {
      parsedQuarters[p.id] = parseFloat(quarters[p.id]) || 0;
    }
    setSaving(true);
    try {
      await onSave({
        ...holeData,
        gross_scores: scores,
        points_delta: parsedQuarters,
      });
      onClose();
    } catch {
      // parent handles errors
    } finally {
      setSaving(false);
    }
  }, [holeData, scores, quarters, players, onSave, onClose]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  if (!isOpen || !holeData) return null;

  return (
    <div
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000, padding: '20px',
      }}
      onClick={onClose}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-hole-title"
    >
      <div
        style={{
          maxWidth: '420px', width: '100%', padding: '20px',
          background: theme.colors.paper, borderRadius: '16px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        }}
        onClick={e => e.stopPropagation()}
      >
        <h3
          id="edit-hole-title"
          style={{
            margin: '0 0 16px', color: theme.colors.primary, fontSize: '20px',
          }}
        >
          Edit Hole {holeData.hole}
        </h3>

        {/* Column headers */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 80px 120px',
          gap: '8px', marginBottom: '8px', padding: '0 4px',
          fontSize: '12px', fontWeight: 'bold', color: theme.colors.textSecondary,
        }}>
          <div>Player</div>
          <div style={{ textAlign: 'center' }}>Strokes</div>
          <div style={{ textAlign: 'center' }}>Quarters</div>
        </div>

        {/* Player rows */}
        {players.map(player => {
          const qVal = parseFloat(quarters[player.id]) || 0;
          return (
            <div
              key={player.id}
              style={{
                display: 'grid', gridTemplateColumns: '1fr 80px 120px',
                gap: '8px', alignItems: 'center',
                padding: '8px 4px',
                borderBottom: `1px solid ${theme.colors.border}`,
              }}
            >
              <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                {player.name}
              </div>

              {/* Strokes */}
              <input
                type="text"
                inputMode="numeric"
                value={scores[player.id] ?? ''}
                onChange={e => {
                  const v = e.target.value;
                  if (v === '' || /^\d+$/.test(v)) {
                    setScores({ ...scores, [player.id]: v === '' ? '' : parseInt(v, 10) });
                  }
                }}
                style={{
                  width: '100%', padding: '8px', fontSize: '16px', fontWeight: 'bold',
                  border: `2px solid ${theme.colors.border}`, borderRadius: '8px',
                  textAlign: 'center', outline: 'none', boxSizing: 'border-box',
                  background: theme.colors.paper,
                  color: theme.colors.textPrimary,
                }}
              />

              {/* Quarters with +/- flip */}
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="-?[0-9]*\.?[0-9]*"
                  value={quarters[player.id] ?? ''}
                  onChange={e => {
                    const v = e.target.value;
                    if (v === '' || v === '-' || /^-?\d*\.?\d*$/.test(v)) {
                      setQuarters({ ...quarters, [player.id]: v });
                    }
                  }}
                  style={{
                    width: '60px', padding: '8px', fontSize: '16px', fontWeight: 'bold',
                    border: `2px solid ${qVal > 0 ? '#4CAF50' : qVal < 0 ? '#f44336' : theme.colors.border}`,
                    borderRadius: '8px', textAlign: 'center', outline: 'none',
                    color: qVal > 0 ? '#4CAF50' : qVal < 0 ? '#f44336' : theme.colors.textPrimary,
                    background: theme.colors.paper,
                    boxSizing: 'border-box',
                  }}
                />
                <button
                  onClick={() => {
                    const base = parseFloat(quarters[player.id]) || 0;
                    if (base !== 0) {
                      setQuarters({ ...quarters, [player.id]: (-base).toString() });
                    }
                  }}
                  className="touch-optimized"
                  style={{
                    width: '32px', height: '32px', borderRadius: '6px',
                    border: `1px solid ${qVal < 0 ? '#66BB6A' : '#EF5350'}`,
                    background: qVal < 0 ? '#E8F5E9' : '#FFEBEE',
                    color: qVal < 0 ? '#2E7D32' : '#C62828',
                    fontWeight: 'bold', fontSize: '11px',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    opacity: qVal === 0 ? 0.4 : 1, flexShrink: 0,
                  }}
                >
                  +/−
                </button>
              </div>
            </div>
          );
        })}

        {/* Zero-sum indicator */}
        {(() => {
          const sum = players.reduce((acc, p) => acc + (parseFloat(quarters[p.id]) || 0), 0);
          const balanced = Math.abs(sum) < 0.01;
          return (
            <div style={{
              marginTop: '12px', padding: '8px 12px', borderRadius: '8px',
              background: balanced ? 'rgba(76,175,80,0.1)' : 'rgba(244,67,54,0.1)',
              color: balanced ? '#4CAF50' : '#f44336',
              fontSize: '13px', fontWeight: 'bold', textAlign: 'center',
            }}>
              {balanced ? '✓ Quarters balanced' : `⚠ Quarters sum: ${sum > 0 ? '+' : ''}${sum}`}
            </div>
          );
        })()}

        {/* Actions */}
        <div style={{
          display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px',
        }}>
          <button
            onClick={onClose}
            className="touch-optimized"
            style={{
              padding: '10px 20px', fontSize: '16px', fontWeight: 'bold',
              border: `1px solid ${theme.colors.border}`, borderRadius: '8px',
              background: 'transparent', color: theme.colors.textPrimary, cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="touch-optimized"
            style={{
              padding: '10px 20px', fontSize: '16px', fontWeight: 'bold',
              border: 'none', borderRadius: '8px',
              background: theme.colors.primary, color: 'white', cursor: 'pointer',
              opacity: saving ? 0.6 : 1,
            }}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};

EditHoleModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired,
  holeData: PropTypes.object,
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
  })).isRequired,
};

export default EditHoleModal;
