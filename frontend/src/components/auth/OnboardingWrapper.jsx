import React from 'react';
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
  const { isAuthenticated, isLoading: authLoading } = useAuth0();
  const {
    loading: profileLoading,
    needsLegacyName,
    legacyNameSuggestion,
    updateLegacyName,
    skipLegacyName
  } = usePlayerProfile();

  // Don't show modal while loading
  if (authLoading || profileLoading) {
    return children;
  }

  // Only show for authenticated users who need to set legacy name
  if (!isAuthenticated || !needsLegacyName) {
    return children;
  }

  // Fuzzy legacy-name match to SUGGEST (not auto-linked). The backend returns
  // this as legacy_name_suggestion; the account's legacy_name stays null until
  // the user explicitly confirms in the modal.
  const suggestedName = legacyNameSuggestion || null;

  return (
    <>
      {children}
      <OnboardingModal
        onComplete={() => {
          // Onboarding complete
        }}
        onSkip={skipLegacyName}
        updateLegacyName={updateLegacyName}
        suggestedName={suggestedName}
      />
    </>
  );
};

export default OnboardingWrapper;
