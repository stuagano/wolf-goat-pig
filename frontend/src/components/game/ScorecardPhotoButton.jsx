import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { apiConfig } from '../../config/api.config';
import ScorecardPhotoZoom from './ScorecardPhotoZoom';

const API_URL = apiConfig.baseUrl;

/**
 * ScorecardPhotoButton — shows a "📷 Photo" button when the saved round has a
 * scorecard photo on the server. Clicking opens the full-screen zoom overlay.
 * Renders nothing when the photo endpoint returns a non-OK response.
 */
const ScorecardPhotoButton = ({ gameId }) => {
  const [hasPhoto, setHasPhoto] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!gameId) return;
    fetch(`${API_URL}/games/${gameId}/scorecard-photo`)
      .then((res) => setHasPhoto(res.ok))
      .catch(() => setHasPhoto(false));
  }, [gameId]);

  if (!hasPhoto) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        style={{
          padding: '12px 24px',
          fontSize: '16px',
          fontWeight: 'bold',
          borderRadius: '8px',
          border: '2px solid #1976d2',
          background: 'white',
          color: '#1976d2',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
      >
        📷 Photo
      </button>
      {isOpen && (
        <ScorecardPhotoZoom
          src={`${API_URL}/games/${gameId}/scorecard-photo`}
          onClose={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

ScorecardPhotoButton.propTypes = {
  gameId: PropTypes.string.isRequired,
};

export default ScorecardPhotoButton;
