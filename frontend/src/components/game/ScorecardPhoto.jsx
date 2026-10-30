import React, { useState, useEffect, useRef } from 'react';
import ScorecardCapture from './ScorecardCapture';
import ScorecardReview from './ScorecardReview';
import GHINPostModal from './GHINPostModal';
import { apiConfig } from '../../config/api.config';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { preprocessScorecardImage, downscaleToBase64 } from '../../utils/scorecardImage';
import { readDraft, keepDraft, clearDraft, extractionFromQuarters } from './roundWriteDraft';

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
  const authenticatedFetch = useAuthenticatedFetch();
  // 'capture' | 'processing' | 'review' | 'saving' | 'ghin_prompt' | 'error'
  const [stage, setStage] = useState(initialStage || 'capture');
  const [extraction, setExtraction] = useState(initialExtraction || null);
  const [savedQuarters, setSavedQuarters] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [photoUrl, setPhotoUrl] = useState(null);
  const photoUrlRef = useRef(null);
  const photoB64Ref = useRef(null);
  const photoFileRef = useRef(null);
  const retainedSubmission = mode === 'attach' ? readDraft(gameId, 'attach') : null;
  const submissionRef = useRef(retainedSubmission ? {
    key: retainedSubmission.key, content: JSON.stringify(retainedSubmission.quarters),
  } : null);
  const reviewedSnapshot = useRef(null);
  const [photoWarning, setPhotoWarning] = useState('');
  // Held attach edits live locally only; reapply is an explicit user action.
  const [held, setHeld] = useState(() => (mode === 'attach' ? readDraft(gameId, 'attach') : null));
  const reloadAccepted = async () => {
    try {
      const res = await authenticatedFetch(`${API_URL}/games/${gameId}/state`);
      if (!res.ok) throw new Error('Could not reload the accepted round. Your edits are retained locally.');
      const snapshot = await res.json();
      if (!Number.isInteger(snapshot.revision)) throw new Error('Round revision unavailable; nothing was submitted.');
      reviewedSnapshot.current = snapshot;
      const next = { ...held, revision: snapshot.revision };
      keepDraft(gameId, 'attach', next);
      setHeld(next);
      setExtraction(extractionFromQuarters(players, next.quarters));
      setErrorMsg(null);
      setStage('review');
    } catch (err) { setErrorMsg(err.message); }
  };
  // Free the retained object URL when this flow unmounts.
  useEffect(() => () => { if (photoUrlRef.current) URL.revokeObjectURL(photoUrlRef.current); }, []);

  const enterManually = () => {
    const roster = players.length ? players : pickedPlayers.map(name => ({ name }));
    setExtraction(buildBlankExtraction(roster));
    setStage('review');
  };

  const handleCapture = async (file) => {
    photoFileRef.current = file;
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
    downscaleToBase64(file, 1200).then((b64) => { photoB64Ref.current = b64; }).catch(() => {});

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
        const body = JSON.stringify({ ...payload, image_base64: photoB64Ref.current || undefined });
        if (!submissionRef.current || submissionRef.current.body !== body) {
          submissionRef.current = { body, key: crypto.randomUUID() };
        }
        const res = await authenticatedFetch(`${API_URL}/games/from-scorecard`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Idempotency-Key': submissionRef.current.key },
          body: submissionRef.current.body,
        });
        if (!res.ok) {
          const detail = await res.json().catch(() => ({}));
          throw new Error(detail.detail || `Save failed: ${res.status}`);
        }
        const data = await res.json();
        if (res.status === 202) {
          setErrorMsg('Round identity needs review. No duplicate round was created.');
          setStage('conflict');
          return;
        }
        onSaved(data); // skip GHIN on this path
        return;
      }

      const holeQuarters = payload;
      if (!submissionRef.current || submissionRef.current.content !== JSON.stringify(holeQuarters)) {
        submissionRef.current = { content: JSON.stringify(holeQuarters), key: crypto.randomUUID() };
      }
      keepDraft(gameId, 'attach', { quarters: holeQuarters, revision: held?.revision, key: submissionRef.current.key });
      let snapshot = reviewedSnapshot.current;
      if (!snapshot) {
        const current = await authenticatedFetch(`${API_URL}/games/${gameId}/state`);
        if (!current.ok) throw new Error('Reload the round before attaching scores.');
        snapshot = await current.json();
      }
      if (!Number.isInteger(snapshot.revision)) throw new Error('Round revision unavailable; nothing was submitted.');
      // Whole-snapshot semantics: keep server holes this card does not cover.
      const submitted = new Set(Object.keys(holeQuarters).map(h => parseInt(h, 10)));
      const holes = [
        ...(snapshot.hole_history || [])
          .filter(h => !submitted.has(h.hole))
          .map(h => ({ hole_number: h.hole, quarters: h.points_delta, gross_scores: h.gross_scores || null, notes: h.notes || null, teams: h.teams || null })),
        ...Object.keys(holeQuarters).map(holeStr => ({
          hole_number: parseInt(holeStr, 10),
          quarters: holeQuarters[holeStr],
        })),
      ];
      const res = await authenticatedFetch(`${API_URL}/games/${gameId}/scores`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': submissionRef.current.key },
        body: JSON.stringify({ holes, current_hole: 18, expected_revision: snapshot.revision }),
      });

      if (photoFileRef.current) {
        try {
          const form = new FormData();
          form.append('file', photoFileRef.current);
          const photo = await authenticatedFetch(`${API_URL}/games/${gameId}/scorecard-photo`, { method: 'PUT', body: form });
          if (!photo.ok) throw new Error('Photo upload failed');
        } catch {
          setPhotoWarning('Scores were submitted, but the photo was not saved. Attach the photo separately; do not create another round.');
        }
      }
      if (res.status === 409) {
        const rejected = await res.json().catch(() => ({}));
        const draft = { quarters: holeQuarters, revision: snapshot.revision, key: submissionRef.current.key, response: rejected };
        keepDraft(gameId, 'attach', draft);
        setHeld(draft);
        reviewedSnapshot.current = null;
        // Existing issue IDs can predate this stale request, so none proves
        // that these particular edits were staged.
        setErrorMsg('Round changed. Your edited scores are retained locally; this response does not confirm server staging. Reload accepted round, review, then explicitly confirm again.');
        setStage('conflict');
        return;
      }
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(typeof detail.detail === 'string' ? detail.detail : `Save failed: ${res.status}`);
      }

      clearDraft(gameId, 'attach');
      setHeld(null);
      setSavedQuarters(holeQuarters);
      setStage('ghin_prompt');
    } catch (err) {
      setErrorMsg(err.message || 'Failed to save quarters');
      setStage('error');
    }
  };

  if (held && !reviewedSnapshot.current && stage !== 'saving' && stage !== 'conflict') {
    return <div role="alert"><p>{errorMsg || 'Unaccepted edits are retained locally. Reload before reviewing and explicitly resubmitting.'}</p>
      <button onClick={reloadAccepted}>Reload accepted round and reapply my retained edits</button>
      <button onClick={onCancel}>Close</button></div>;
  }

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

  if (stage === 'conflict') {
    return <div role="alert"><p>{errorMsg}</p><p>{photoWarning}</p>
      <a href={gameId ? `/game/${gameId}` : '/rounds/reconciliation'}>Open review / reload round</a>
      {held && <button onClick={reloadAccepted}>Reload accepted round and reapply my retained edits</button>}
      <button onClick={onCancel}>Close</button></div>;
  }

  if (stage === 'ghin_prompt') {
    return (
      <><p role="status">{photoWarning}</p><GHINPostModal
        players={players}
        playedAt={new Date().toISOString().slice(0, 10)}
        onPosted={() => onSaved(savedQuarters)}
        onSkip={() => onSaved(savedQuarters)}
      /></>
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
