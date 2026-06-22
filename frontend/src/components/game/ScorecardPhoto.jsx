import React, { useState, useEffect, useRef } from 'react';
import ScorecardCapture from './ScorecardCapture';
import ScorecardReview from './ScorecardReview';
import GHINPostModal from './GHINPostModal';
import { apiConfig } from '../../config/api.config';
import { preprocessScorecardImage } from '../../utils/scorecardImage';

const API_URL = apiConfig.baseUrl;

/**
 * ScorecardPhoto — orchestrates the full scorecard photo flow:
 *   capture → processing → review → save
 *
 * Props:
 *   gameId     — the current game ID (unused in 'new-round' mode)
 *   players    — array of { id, name } player objects (in tee order)
 *   onSaved    — called with saved scores payload after successful save
 *   onCancel   — called to dismiss without saving
 *   mode       — 'attach' (default) saves to the current game; 'new-round'
 *                records a standalone round via /games/from-scorecard
 *   rosterNames — roster names passed through to ScorecardReview for mapping
 *   initialStage / initialExtraction — test seam to seed state directly
 */
/** Build a blank extraction so ScorecardReview opens with all cells empty */
const buildBlankExtraction = (players) => ({
  players: players.map(p => ({ name: p.name, confidence: 1.0 })),
  running_totals: [],
  per_hole_scores: [],
});

const ScorecardPhoto = ({
  gameId,
  players,
  onSaved,
  onCancel,
  mode = 'attach',
  rosterNames = [],
  pickedPlayers = [],
  initialStage,
  initialExtraction,
}) => {
  // 'capture' | 'processing' | 'review' | 'saving' | 'ghin_prompt' | 'error'
  const [stage, setStage] = useState(initialStage || 'capture');
  const [extraction, setExtraction] = useState(initialExtraction || null);
  const [savedQuarters, setSavedQuarters] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [photoUrl, setPhotoUrl] = useState(null);
  const photoUrlRef = useRef(null);
  // Free the retained object URL when this flow unmounts.
  useEffect(() => () => { if (photoUrlRef.current) URL.revokeObjectURL(photoUrlRef.current); }, []);

  const enterManually = () => {
    setExtraction(buildBlankExtraction(players));
    setStage('review');
  };

  const handleCapture = async (file) => {
    setStage('processing');
    setErrorMsg(null);

    // Retain the ORIGINAL photo (sharpest, no preprocessing marks) so the review
    // screen can zoom in to validate the scanned totals. Best-effort: if object
    // URLs aren't available, skip the zoom rather than break the scan.
    try {
      if (photoUrlRef.current) URL.revokeObjectURL(photoUrlRef.current);
      const url = URL.createObjectURL(file);
      photoUrlRef.current = url;
      setPhotoUrl(url);
    } catch {
      // no object URL support in this context — proceed without in-app photo zoom
    }

    // Auto-orient via EXIF and downscale oversized phone shots before
    // upload — much cleaner input for the vision model and ~5–10x less
    // bandwidth from a 4032px iPhone capture.
    const prepped = await preprocessScorecardImage(file);

    const formData = new FormData();
    formData.append('file', prepped);
    if (pickedPlayers.length > 0) {
      formData.append('players', JSON.stringify(pickedPlayers));
    }

    try {
      const res = await fetch(`${API_URL}/scorecard/scan`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = body.detail;
        const msg = Array.isArray(detail)
          ? detail.map(e => e.msg || JSON.stringify(e)).join(', ')
          : (typeof detail === 'string' ? detail : `Server error ${res.status}`);
        throw new Error(msg);
      }

      const data = await res.json();
      setExtraction(data);
      setStage('review');
    } catch (err) {
      setErrorMsg(err.message || 'Failed to scan scorecard');
      setStage('error');
    }
  };

  const handleConfirm = async (payload) => {
    setStage('saving');
    setErrorMsg(null);

    try {
      if (mode === 'new-round') {
        const res = await fetch(`${API_URL}/games/from-scorecard`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...payload, course_name: 'Wing Point' }),
        });
        if (!res.ok) {
          const detail = await res.json().catch(() => ({}));
          throw new Error(detail.detail || `Save failed: ${res.status}`);
        }
        const data = await res.json();
        onSaved(data); // skip GHIN on this path
        return;
      }

      const holeQuarters = payload;
      const holes = Object.keys(holeQuarters).map(holeStr => ({
        hole_number: parseInt(holeStr, 10),
        quarters: holeQuarters[holeStr],
      }));
      const res = await fetch(`${API_URL}/games/${gameId}/scores`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ holes, current_hole: 18 }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `Save failed: ${res.status}`);
      }

      setSavedQuarters(holeQuarters);
      setStage('ghin_prompt');
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
        onManualEntry={enterManually}
      />
    );
  }

  if (stage === 'processing') {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
        <div className="animate-spin text-4xl">⏳</div>
        <p className="text-gray-600 font-medium">Reading scorecard...</p>
        <p className="text-sm text-gray-400">Reading the scorecard. This takes a few seconds.</p>
      </div>
    );
  }

  if (stage === 'review' && extraction) {
    return (
      <ScorecardReview
        extraction={extraction}
        players={players}
        mode={mode}
        rosterNames={rosterNames}
        pickedPlayers={pickedPlayers}
        photoUrl={photoUrl}
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

  if (stage === 'ghin_prompt') {
    return (
      <GHINPostModal
        players={players}
        playedAt={new Date().toISOString().slice(0, 10)}
        onPosted={() => onSaved(savedQuarters)}
        onSkip={() => onSaved(savedQuarters)}
      />
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
            onClick={enterManually}
            className="flex-1 py-3 bg-gray-700 text-white rounded-xl font-semibold hover:bg-gray-800 transition-colors"
          >
            Enter Manually
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
