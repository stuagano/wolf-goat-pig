/**
 * EditHoleModal - Shared modal component for editing hole data
 *
 * Consolidates the edit hole modal that was duplicated in:
 * - Scorecard.jsx
 * - SimpleScorekeeper.jsx
 *
 * Provides a consistent UI for editing strokes and quarters.
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';
import { Card, Button, Input } from '../ui';
import { useScoreValidation, SCORE_CONSTRAINTS } from '../../hooks/useScoreValidation';

/**
 * EditHoleModal Component
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether the modal is open
 * @param {Function} props.onClose - Callback when modal is closed
 * @param {Function} props.onSave - Callback when changes are saved ({ hole, playerId, strokes, quarters })
 * @param {number} props.holeNumber - The hole number being edited
 * @param {string} props.playerName - Name of the player
 * @param {string} props.playerId - ID of the player
 * @param {number} props.currentStrokes - Current strokes value
 * @param {number} props.currentQuarters - Current quarters value
 * @param {boolean} props.showQuartersOverride - Whether to show the quarters override field
 */
const EditHoleModal = ({
  isOpen,
  onClose,
  onSave,
  holeNumber,
  playerName,
  playerId,
  currentStrokes = null,
  currentQuarters = 0,
  showQuartersOverride = true
}) => {
  const theme = useTheme();
  const { validateStrokes, validateQuarters } = useScoreValidation();

  const [strokes, setStrokes] = useState('');
  const [quarters, setQuarters] = useState('');
  const [errors, setErrors] = useState({ strokes: null, quarters: null });

  // Reset form when modal opens or data changes
  useEffect(() => {
    if (isOpen) {
      setStrokes(currentStrokes !== null ? currentStrokes.toString() : '');
      setQuarters(currentQuarters !== null ? currentQuarters.toString() : '0');
      setErrors({ strokes: null, quarters: null });
    }
  }, [isOpen, currentStrokes, currentQuarters]);

  const handleStrokesChange = useCallback((e) => {
    const value = e.target.value;
    setStrokes(value);
    if (value !== '') {
      const validation = validateStrokes(value);
      setErrors(prev => ({ ...prev, strokes: validation.error }));
    } else {
      setErrors(prev => ({ ...prev, strokes: null }));
    }
  }, [validateStrokes]);

  const handleQuartersChange = useCallback((e) => {
    const value = e.target.value;
    setQuarters(value);
    if (value !== '') {
      const validation = validateQuarters(value);
      setErrors(prev => ({ ...prev, quarters: validation.error }));
    } else {
      setErrors(prev => ({ ...prev, quarters: null }));
    }
  }, [validateQuarters]);

  const handleSave = useCallback(() => {
    // Validate strokes
    const strokesValidation = validateStrokes(strokes);
    if (!strokesValidation.valid) {
      setErrors(prev => ({ ...prev, strokes: strokesValidation.error }));
      return;
    }

    // Validate quarters if shown
    let quartersValue = 0;
    if (showQuartersOverride) {
      const quartersValidation = validateQuarters(quarters);
      if (!quartersValidation.valid) {
        setErrors(prev => ({ ...prev, quarters: quartersValidation.error }));
        return;
      }
      quartersValue = quartersValidation.value;
    }

    onSave({
      hole: holeNumber,
      playerId,
      strokes: strokesValidation.value,
      quarters: quartersValue
    });

    onClose();
  }, [strokes, quarters, holeNumber, playerId, showQuartersOverride, validateStrokes, validateQuarters, onSave, onClose]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      onClose();
    }
  }, [handleSave, onClose]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px'
      }}
      onClick={onClose}
      onKeyDown={handleKeyPress}
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-hole-title"
    >
      <Card
        style={{
          maxWidth: '400px',
          width: '100%',
          padding: '24px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <h3
          id="edit-hole-title"
          style={{
            marginTop: 0,
            marginBottom: '20px',
            color: theme.colors.primary,
            fontSize: '20px'
          }}
        >
          Edit Hole {holeNumber} - {playerName}
        </h3>

        {/* Strokes Input */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontWeight: 'bold',
            color: theme.colors.textPrimary
          }}>
            Strokes (Gross Score):
          </label>
          <Input
            type="number"
            value={strokes}
            onChange={handleStrokesChange}
            min={SCORE_CONSTRAINTS.MIN_STROKES}
            max={SCORE_CONSTRAINTS.MAX_STROKES}
            autoFocus
            variant="inline"
            inputStyle={{
              width: '100%',
              padding: '12px',
              fontSize: '16px',
              border: `2px solid ${errors.strokes ? theme.colors.error : theme.colors.border}`,
              borderRadius: '8px',
              boxSizing: 'border-box'
            }}
          />
          <p style={{
            fontSize: '12px',
            color: errors.strokes ? theme.colors.error : theme.colors.textSecondary,
            marginTop: '4px',
            marginBottom: 0
          }}>
            {errors.strokes || `Actual number of strokes taken (${SCORE_CONSTRAINTS.MIN_STROKES}-${SCORE_CONSTRAINTS.MAX_STROKES})`}
          </p>
        </div>

        {/* Quarters Override Input */}
        {showQuartersOverride && (
          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontWeight: 'bold',
              color: theme.colors.textPrimary
            }}>
              Quarters (Manual Override):
            </label>
            <Input
              type="number"
              value={quarters}
              onChange={handleQuartersChange}
              min={SCORE_CONSTRAINTS.MIN_QUARTERS}
              max={SCORE_CONSTRAINTS.MAX_QUARTERS}
              step="0.5"
              variant="inline"
              inputStyle={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                border: `2px solid ${errors.quarters ? theme.colors.error : theme.colors.warning || '#ff9800'}`,
                borderRadius: '8px',
                backgroundColor: 'rgba(255, 152, 0, 0.05)',
                boxSizing: 'border-box'
              }}
            />
            <p style={{
              fontSize: '12px',
              color: errors.quarters ? theme.colors.error : theme.colors.textSecondary,
              marginTop: '4px',
              marginBottom: 0
            }}>
              {errors.quarters || (
                <>
                  Override automatic quarter calculation. Use when scores are correct but quarters are wrong.
                  <br />
                  Positive for winning (+), negative for losing (-)
                </>
              )}
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{
          display: 'flex',
          gap: '12px',
          justifyContent: 'flex-end'
        }}>
          <Button
            variant="secondary"
            onClick={onClose}
            style={{
              padding: '10px 20px',
              fontSize: '16px'
            }}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={!!errors.strokes || (showQuartersOverride && !!errors.quarters)}
            style={{
              padding: '10px 20px',
              fontSize: '16px'
            }}
          >
            Save
          </Button>
        </div>
      </Card>
    </div>
  );
};

EditHoleModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired,
  holeNumber: PropTypes.number,
  playerName: PropTypes.string,
  playerId: PropTypes.string,
  currentStrokes: PropTypes.number,
  currentQuarters: PropTypes.number,
  showQuartersOverride: PropTypes.bool
};

export default EditHoleModal;
