import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { apiConfig } from '../../config/api.config';
import ScorecardPhotoZoom from './ScorecardPhotoZoom';
import CardExtractionValidation from './CardExtractionValidation';
import './RoundCardReview.css';

/** A view-only reference pane around the existing completed-round score UI. */
const RoundCardReview = ({ gameId, photoVersion = 0, players, holeHistory, uploading = false, children }) => {
  const [attempt, setAttempt] = useState(0);
  const [status, setStatus] = useState('loading');
  // Readiness belongs to the loaded URL, not the previous photo's status.
  const [loadedSrc, setLoadedSrc] = useState(null);
  const [height, setHeight] = useState(240);
  const src = `${apiConfig.baseUrl}/games/${gameId}/scorecard-photo?v=${photoVersion}&retry=${attempt}`;

  useEffect(() => {
    const controller = new AbortController();
    setStatus('loading');
    fetch(src, { signal: controller.signal })
      .then((res) => {
        if (!controller.signal.aborted) setStatus(res.ok ? 'decoding' : res.status === 404 ? 'missing' : 'error');
      })
      .catch(() => { if (!controller.signal.aborted) setStatus('error'); });
    return () => controller.abort();
  }, [src]);

  return (
    <section className="round-card-review" aria-label="Review card & scores">
      <header className="round-card-review__heading">
        <h2>Review card &amp; scores</h2>
        <p>Compare the paper card with the recorded round.</p>
      </header>
      <div className="round-card-review__grid">
        <aside className="round-card-review__photo" aria-label="Paper card">
          <h3>Paper card</h3>
          <label className="round-card-review__resize">
            Photo panel height
            <input type="range" min="160" max="360" step="20" value={height} onChange={(e) => setHeight(Number(e.target.value))} />
          </label>
          <div className="round-card-review__viewport" style={{ '--photo-height': `${height}px` }}>
            {(status === 'loading' || status === 'decoding') && <p role="status">Loading card photo…</p>}
            {(status === 'decoding' || status === 'ready') && (
              <ScorecardPhotoZoom key={src} src={src} embedded onLoad={() => { setLoadedSrc(src); setStatus('ready'); }} onError={() => setStatus('error')} />
            )}
            {(status === 'missing' || status === 'error') && (
              <div className="round-card-review__message" role="status">
                <p>{status === 'missing' ? 'No card photo has been saved for this round.' : 'Could not load the card photo. Recorded scores are still available.'}</p>
                <button type="button" onClick={() => setAttempt((n) => n + 1)}>Retry photo</button>
              </div>
            )}
          </div>
        </aside>
        <div className="round-card-review__scores" aria-label="Recorded scores" role="region">
          <h3>Recorded scores</h3>
          {players && loadedSrc === src && status === 'ready' && !uploading && (
            <CardExtractionValidation photoSrc={src} players={players} holeHistory={holeHistory} />
          )}
          {children}
        </div>
      </div>
    </section>
  );
};

RoundCardReview.propTypes = {
  gameId: PropTypes.string.isRequired,
  photoVersion: PropTypes.number,
  players: PropTypes.array,
  holeHistory: PropTypes.array,
  uploading: PropTypes.bool,
  children: PropTypes.node.isRequired,
};

export default RoundCardReview;
