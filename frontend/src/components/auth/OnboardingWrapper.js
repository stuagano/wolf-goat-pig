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
    profile,
    loading: profileLoading,
    needsLegacyName,
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

  // Calculate suggested name based on fuzzy match (if any)
  // The backend already attempted this, so check if profile has a suggestion
  const suggestedName = profile?.legacy_name || null;

  return (
    <>
      {children}
      <OnboardingModal
        onComplete={(legacyName) => {
          console.log('Onboarding complete, linked to:', legacyName);
        }}
        onSkip={skipLegacyName}
        updateLegacyName={updateLegacyName}
        suggestedName={suggestedName}
      />
    </>
  );
};

export default OnboardingWrapper;
