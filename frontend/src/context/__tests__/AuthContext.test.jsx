import React from 'react';
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { render } from '@testing-library/react';
import { AuthProvider } from '../AuthContext';

// Capture the exact props AuthProvider hands to Auth0Provider — this is what
// pins the useRefreshTokens/offline_access pairing so a future edit that
// breaks it fails here in CI, not as a runtime-only "Missing Refresh Token"
// error days later on an expired session.
let capturedProps = null;
vi.mock('@auth0/auth0-react', () => ({
  Auth0Provider: (props) => {
    capturedProps = props;
    return props.children;
  },
}));

describe('AuthProvider Auth0 configuration', () => {
  beforeEach(() => {
    capturedProps = null;
    vi.stubEnv('VITE_AUTH0_DOMAIN', 'test.auth0.com');
    vi.stubEnv('VITE_AUTH0_CLIENT_ID', 'test-client-id');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  test('requests offline_access scope whenever useRefreshTokens is enabled', () => {
    render(
      <AuthProvider>
        <div>child</div>
      </AuthProvider>,
    );

    expect(capturedProps).not.toBeNull();
    if (capturedProps.useRefreshTokens) {
      expect(capturedProps.authorizationParams.scope).toContain('offline_access');
    }
  });

  test('enables the refresh-token fallback so a missing refresh token recovers via silent auth', () => {
    render(
      <AuthProvider>
        <div>child</div>
      </AuthProvider>,
    );

    expect(capturedProps).not.toBeNull();
    // Without this, an expired/absent refresh token throws "Missing Refresh
    // Token" with no recovery path instead of falling back to a silent iframe.
    if (capturedProps.useRefreshTokens) {
      expect(capturedProps.useRefreshTokensFallback).toBe(true);
    }
  });
});
