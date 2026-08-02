import { describe, test, expect, vi, afterEach } from "vitest";
import { acquireAccessToken, isRecoverableAuthError } from "../authToken";

describe("apiTokenOptions", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  // Pins the fix for club-player linking not tying into OAuth users: every token
  // acquisition must request our backend API audience, not just rely on the
  // Auth0Provider default (a silent refresh can otherwise mint an /userinfo-only
  // token the backend rejects). Evaluated at import, so stub the env then re-import.
  test("requests the API audience when VITE_AUTH0_AUDIENCE is set", async () => {
    vi.stubEnv("VITE_AUTH0_AUDIENCE", "https://api.example.com");
    vi.resetModules();
    const { apiTokenOptions } = await import("../authToken");
    expect(apiTokenOptions).toEqual({
      authorizationParams: { audience: "https://api.example.com" },
    });
  });

  test("is undefined when no audience is configured", async () => {
    vi.stubEnv("VITE_AUTH0_AUDIENCE", "");
    vi.resetModules();
    const { apiTokenOptions } = await import("../authToken");
    expect(apiTokenOptions).toBeUndefined();
  });
});

describe("withApiAudience", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  const importWithAudience = async (audience) => {
    vi.stubEnv("VITE_AUTH0_AUDIENCE", audience);
    vi.resetModules();
    return import("../authToken");
  };

  // Regression guard for the audience-less `useAccessToken().getToken()` path:
  // Auth0 minted an opaque token the backend rejected as "Not enough segments".
  test("pins the API audience when called with no options", async () => {
    const { withApiAudience } = await importWithAudience("https://api.example.com");
    expect(withApiAudience()).toEqual({
      authorizationParams: { audience: "https://api.example.com" },
    });
  });

  test("merges the audience into caller options without dropping them", async () => {
    const { withApiAudience } = await importWithAudience("https://api.example.com");
    expect(withApiAudience({ cacheMode: "off" })).toEqual({
      cacheMode: "off",
      authorizationParams: { audience: "https://api.example.com" },
    });
  });

  test("preserves other authorizationParams alongside the audience", async () => {
    const { withApiAudience } = await importWithAudience("https://api.example.com");
    expect(withApiAudience({ authorizationParams: { scope: "openid profile" } })).toEqual({
      authorizationParams: { audience: "https://api.example.com", scope: "openid profile" },
    });
  });

  test("lets an explicit caller audience win", async () => {
    const { withApiAudience } = await importWithAudience("https://api.example.com");
    expect(withApiAudience({ authorizationParams: { audience: "https://other.example.com" } })).toEqual({
      authorizationParams: { audience: "https://other.example.com" },
    });
  });

  test("passes options through unchanged when no audience is configured", async () => {
    const { withApiAudience } = await importWithAudience("");
    expect(withApiAudience()).toBeUndefined();
    expect(withApiAudience({ cacheMode: "off" })).toEqual({ cacheMode: "off" });
  });
});

describe("isRecoverableAuthError", () => {
  test("returns false for nullish input", () => {
    expect(isRecoverableAuthError(null)).toBe(false);
    expect(isRecoverableAuthError(undefined)).toBe(false);
  });

  test("detects the missing_refresh_token error code", () => {
    expect(isRecoverableAuthError({ error: "missing_refresh_token" })).toBe(true);
  });

  test("detects login_required / consent_required codes", () => {
    expect(isRecoverableAuthError({ error: "login_required" })).toBe(true);
    expect(isRecoverableAuthError({ code: "consent_required" })).toBe(true);
  });

  test("detects the missing-refresh-token message text", () => {
    expect(isRecoverableAuthError(new Error("Missing Refresh Token"))).toBe(true);
  });

  test("returns false for unrelated errors", () => {
    expect(isRecoverableAuthError(new Error("Network request failed"))).toBe(false);
    expect(isRecoverableAuthError({ error: "server_error" })).toBe(false);
  });
});

describe("acquireAccessToken", () => {
  test("returns the token from the first (cached) attempt", async () => {
    const getToken = vi.fn().mockResolvedValue("cached-token");

    await expect(acquireAccessToken(getToken)).resolves.toBe("cached-token");
    expect(getToken).toHaveBeenCalledTimes(1);
    expect(getToken).toHaveBeenCalledWith();
  });

  test("retries with cacheMode:'off' on a missing refresh token", async () => {
    const getToken = vi
      .fn()
      .mockRejectedValueOnce({ error: "missing_refresh_token" })
      .mockResolvedValueOnce("fresh-token");

    await expect(acquireAccessToken(getToken)).resolves.toBe("fresh-token");
    expect(getToken).toHaveBeenCalledTimes(2);
    expect(getToken).toHaveBeenLastCalledWith({ cacheMode: "off" });
  });

  test("does not retry on a non-recoverable error", async () => {
    const err = new Error("boom");
    const getToken = vi.fn().mockRejectedValue(err);

    await expect(acquireAccessToken(getToken)).rejects.toBe(err);
    expect(getToken).toHaveBeenCalledTimes(1);
  });

  test("propagates the error when the cache-off retry also fails", async () => {
    const getToken = vi
      .fn()
      .mockRejectedValueOnce({ error: "missing_refresh_token" })
      .mockRejectedValueOnce({ error: "login_required" });

    await expect(acquireAccessToken(getToken)).rejects.toEqual({ error: "login_required" });
    expect(getToken).toHaveBeenCalledTimes(2);
  });

  test("throws when getAccessTokenSilently is not a function", async () => {
    await expect(acquireAccessToken(undefined)).rejects.toThrow(
      "getAccessTokenSilently is not available",
    );
  });

  test("forwards Auth0 options and preserves them on cache-off retry", async () => {
    const options = { authorizationParams: { audience: "https://example.com" } };
    const getToken = vi
      .fn()
      .mockRejectedValueOnce({ error: "missing_refresh_token" })
      .mockResolvedValueOnce("fresh-token");

    await expect(acquireAccessToken(getToken, options)).resolves.toBe("fresh-token");
    expect(getToken).toHaveBeenNthCalledWith(1, options);
    expect(getToken).toHaveBeenNthCalledWith(2, { ...options, cacheMode: "off" });
  });
});
