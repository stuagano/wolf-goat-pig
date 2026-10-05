import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import OnboardingModal from './OnboardingModal';
import usePlayerProfile from '../../hooks/usePlayerProfile';

/**
 * Wrapper component that shows onboarding modal for new users
 * who haven't linked their account to the legacy tee sheet system.
 *
 * Renders children normally, with the modal overlay when needed.
 */
const OnboardingWrapper = ({ children }) => {
  const { isAuthenticated, isLoading: authLoading, loginWithRedirect } = useAuth0();
  const [findingPlayer, setFindingPlayer] = useState(false);
  const {
    loading: profileLoading,
    needsLegacyName,
    legacyNameSuggestion,
    updateLegacyName,
    skipLegacyName,
    error,
    refetch,
  } = usePlayerProfile();

  const ready = isAuthenticated && !authLoading && !profileLoading;
  const canLink = ready && !error && needsLegacyName;

  // Fuzzy legacy-name match to SUGGEST (not auto-linked). The backend returns
  // this as legacy_name_suggestion; the account's legacy_name stays null until
  // the user explicitly confirms in the modal.
  const suggestedName = legacyNameSuggestion || null;

  return (
    <>
      {ready && error && <div role="alert" style={{ padding: 16, background: '#fff3cd', color: '#332701' }}>
        <strong>Your player profile needs attention.</strong> {error}
        <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
          <button type="button" onClick={refetch}>Try again</button>
          <button type="button" onClick={() => loginWithRedirect({ authorizationParams: { prompt: 'login' } })}>Sign in again</button>
        </div>
      </div>}
      {canLink && !findingPlayer && <section aria-label="Player history" style={{ padding: 16, background: '#eef5ed', color: '#234422' }}>
        <p style={{ marginTop: 0 }}>Already play with the club? Connect your player history once.</p>
        <button type="button" onClick={() => setFindingPlayer(true)}>Find my player history</button>
        {' '}
        <button type="button" onClick={skipLegacyName}>Not now</button>
        <p style={{ marginBottom: 0 }}>You can also do this from Account → Club Player.</p>
      </section>}
      {children}
      {canLink && findingPlayer && <OnboardingModal
        onComplete={() => {
          setFindingPlayer(false);
        }}
        onSkip={() => { setFindingPlayer(false); skipLegacyName(); }}
        updateLegacyName={updateLegacyName}
        suggestedName={suggestedName}
      />}
    </>
  );
};

export default OnboardingWrapper;
