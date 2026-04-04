import React, { useState } from 'react';
import ScorecardCapture from './ScorecardCapture';
import ScorecardReview from './ScorecardReview';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * ScorecardPhoto — orchestrates the full scorecard photo flow:
 *   capture → processing → review → save
 *
 * Props:
 *   gameId     — the current game ID
 *   players    — array of { id, name } player objects (in tee order)
 *   onSaved    — called with saved hole_quarters payload after successful save
 *   onCancel   — called to dismiss without saving
 */
const ScorecardPhoto = ({ gameId, players, onSaved, onCancel }) => {
  // 'capture' | 'processing' | 'review' | 'saving' | 'error'
  const [stage, setStage] = useState('capture');
  const [extraction, setExtraction] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleCapture = async (file) => {
    setStage('processing');
    setErrorMsg(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const res = await fetch(`${API_URL}/scorecard/scan`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `Server error ${res.status}`);
      }

      const data = await res.json();
      setExtraction(data);
      setStage('review');
    } catch (err) {
      setErrorMsg(err.message || 'Failed to scan scorecard');
      setStage('error');
    }
  };

  const handleConfirm = async (holeQuarters) => {
    setStage('saving');
    setErrorMsg(null);

    try {
      const res = await fetch(`${API_URL}/games/${gameId}/quarters-only`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hole_quarters: holeQuarters,
          current_hole: 18,
        }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `Save failed: ${res.status}`);
      }

      onSaved(holeQuarters);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to save quarters');
      setStage('error');
    }
  };

  if (stage === 'capture') {
    return (
      <ScorecardCapture
        onCapture={handleCapture}
        onCancel={onCancel}
      />
    );
  }

  if (stage === 'processing') {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
        <div className="animate-spin text-4xl">⏳</div>
        <p className="text-gray-600 font-medium">Reading scorecard...</p>
        <p className="text-sm text-gray-400">Gemini is extracting the values. This takes a few seconds.</p>
      </div>
    );
  }

  if (stage === 'review' && extraction) {
    return (
      <ScorecardReview
        extraction={extraction}
        players={players}
        onConfirm={handleConfirm}
        onCancel={onCancel}
      />
    );
  }

  if (stage === 'saving') {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
        <div className="animate-spin text-4xl">💾</div>
        <p className="text-gray-600 font-medium">Saving quarters...</p>
      </div>
    );
  }

  if (stage === 'error') {
    return (
      <div className="flex flex-col gap-4 p-4">
        <div className="bg-red-50 border border-red-300 rounded-lg p-4 text-red-700">
          <p className="font-semibold mb-1">Something went wrong</p>
          <p className="text-sm">{errorMsg}</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setStage('capture')}
            className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
          <button
            onClick={onCancel}
            className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return null;
};

export default ScorecardPhoto;
