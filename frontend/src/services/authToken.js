/**
 * Resilient Auth0 access-token acquisition.
 *
 * The app requests refresh tokens (`offline_access` + `useRefreshTokens`). When a
 * cached session predates that config, has third-party cookies blocked, or the
 * refresh token has expired/rotated away, `getAccessTokenSilently()` throws
 * `Missing Refresh Token` (`error === 'missing_refresh_token'`). Left unhandled
 * that surfaces to the user as a hard failure when they try to submit a score.
 *
 * These helpers recover transparently: on a recoverable auth error we retry once
 * with `cacheMode: 'off'`, forcing Auth0 to re-mint a token via the refresh-token
 * fallback (silent `/authorize` iframe — requires `useRefreshTokensFallback` on
 * the provider). If that still fails the caller can prompt a full re-login.
 */

/**
 * Token options that pin every acquisition to our backend API audience.
 *
 * The backend verifies the JWT with `audience=AUTH0_API_AUDIENCE` and rejects
 * anything else. Relying on the `Auth0Provider` default audience is not enough:
 * once `offline_access`/`useRefreshTokens` is on, a silent refresh can mint a
 * token for the default OIDC (`/userinfo`) audience instead of our API. The
 * backend then rejects it as an invalid token (401), which silently breaks
 * `/players/me` and the club-player → OAuth link. Passing the audience on every
 * call keeps each request pinned to the API regardless of how the token is
 * minted. `undefined` when unset so tests and audience-less setups are unchanged.
 */
export const apiTokenOptions = import.meta.env.VITE_AUTH0_AUDIENCE
  ? { authorizationParams: { audience: import.meta.env.VITE_AUTH0_AUDIENCE } }
  : undefined;

/**
 * Merge the API audience into caller-supplied token options.
 *
 * Opting in per call site is how the audience got missed on `useAccessToken`
 * (every `getToken()` there minted an audience-less, opaque token the backend
 * rejected with "Not enough segments"). Wrapping at the hook boundary makes the
 * audience the default rather than something each caller must remember. An
 * explicit `authorizationParams.audience` from the caller still wins.
 *
 * @param {object} [options] - Auth0 `getAccessTokenSilently` options
 * @returns {object|undefined} options pinned to the API audience
 */
export const withApiAudience = (options) => {
  if (!apiTokenOptions) return options;
  if (!options) return apiTokenOptions;
  return {
    ...options,
    authorizationParams: {
      ...apiTokenOptions.authorizationParams,
      ...options.authorizationParams,
    },
  };
};

// Auth0 error codes that mean "the cached credential is gone/stale — get a fresh
// one" rather than a genuine failure we should surface as-is.
const RECOVERABLE_AUTH_ERROR_CODES = new Set([
  "missing_refresh_token",
  "invalid_grant",
  "login_required",
  "consent_required",
  "interaction_required",
]);

/**
 * True when an error thrown by `getAccessTokenSilently` means we should retry
 * with a fresh token (or re-login) rather than treat it as a real failure.
 * @param {unknown} error
 * @returns {boolean}
 */
export const isRecoverableAuthError = (error) => {
  if (!error) return false;
  const code = error.error || error.code || "";
  if (RECOVERABLE_AUTH_ERROR_CODES.has(code)) return true;
  const message = (error.message || error.error_description || "").toLowerCase();
  return (
    message.includes("refresh token") ||
    message.includes("login required") ||
    message.includes("consent required")
  );
};

/**
 * Acquire an Auth0 access token, transparently recovering from a missing or
 * expired refresh token. First attempt uses the cache; on a recoverable auth
 * error it retries once bypassing the cache so Auth0 falls back to a silent
 * `/authorize` iframe.
 *
 * @param {(opts?: object) => Promise<string>} getAccessTokenSilently - Auth0 SDK fn
 * @param {object} [options] - forwarded to getAccessTokenSilently (e.g. audience)
 * @returns {Promise<string>} access token
 */
export const acquireAccessToken = async (getAccessTokenSilently, options = undefined) => {
  if (typeof getAccessTokenSilently !== "function") {
    throw new Error("getAccessTokenSilently is not available");
  }

  try {
    return options === undefined
      ? await getAccessTokenSilently()
      : await getAccessTokenSilently(options);
  } catch (error) {
    if (!isRecoverableAuthError(error)) {
      throw error;
    }
    // Bypass the cache so the SDK re-mints a token via the refresh-token
    // fallback rather than reusing the missing/expired one.
    const retryOptions = options === undefined
      ? { cacheMode: "off" }
      : { ...options, cacheMode: "off" };
    return await getAccessTokenSilently(retryOptions);
  }
};

export default acquireAccessToken;
