import React, { useState, useRef, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import LegacyNameSelector from './LegacyNameSelector';

/**
 * Modal shown to new users to link their account to the legacy tee sheet system
 * Appears on first login when legacy_name is not set
 */
const OnboardingModal = ({
  onComplete,
  onSkip,
  updateLegacyName,
  suggestedName = null
}) => {
  const { user } = useAuth0();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    // Native dialog contains keyboard focus and returns it to the opener.
    if (dialog.showModal) dialog.showModal();
    else dialog.setAttribute('open', '');
    return () => dialog.close?.();
  }, []);

  const handleSelect = async (legacyName) => {
    setSaving(true);
    setError(null);

    try {
      await updateLegacyName(legacyName);
      onComplete(legacyName);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = () => {
    onSkip();
  };

  return (
    <dialog ref={dialogRef} onCancel={(event) => { event.preventDefault(); if (!saving) handleSkip(); }} className="onboarding-modal" aria-labelledby="history-link-title">
        <div className="modal-header">
          <div className="welcome-icon">⛳</div>
          <h2 id="history-link-title">Find my player history</h2>
          <p className="subtitle">Connect your club name to your sign-in.</p>
          <button type="button" onClick={handleSkip} disabled={saving}>Close</button>
        </div>

        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}

        {saving ? (
          <div className="saving-state">
            <div className="spinner"></div>
            <p>Linking your account...</p>
          </div>
        ) : (
          <LegacyNameSelector
            currentName={user?.name || user?.email}
            onSelect={handleSelect}
            onSkip={handleSkip}
            suggestedName={suggestedName}
          />
        )}
      <style jsx>{`
        .onboarding-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 9999;
          padding: 20px;
        }

        .onboarding-modal {
          border: 0;
          padding: 0;
          width: min(480px, calc(100vw - 40px));
          background: white;
          border-radius: 16px;
          max-width: 480px;
          width: 100%;
          max-height: 90vh;
          overflow-y: auto;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }

        .onboarding-modal::backdrop { background: rgba(0, 0, 0, 0.7); }

        .modal-header {
          text-align: center;
          padding: 30px 20px 10px 20px;
          border-bottom: 1px solid #eee;
        }

        .welcome-icon {
          font-size: 48px;
          margin-bottom: 10px;
        }

        .modal-header h2 {
          margin: 0 0 8px 0;
          color: #2d5a27;
          font-size: 24px;
        }

        .subtitle {
          margin: 0;
          color: #666;
          font-size: 14px;
        }

        .error-banner {
          background: #ffebee;
          color: #c62828;
          padding: 12px 20px;
          margin: 15px 20px 0 20px;
          border-radius: 8px;
          font-size: 14px;
        }

        .saving-state {
          padding: 60px 20px;
          text-align: center;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #eee;
          border-top-color: #2d5a27;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px auto;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .saving-state p {
          color: #666;
          margin: 0;
        }
      `}</style>
    </dialog>
  );
};

export default OnboardingModal;
