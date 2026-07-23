import { describe, test, expect, vi } from "vitest";
import { acquireAccessToken, isRecoverableAuthError } from "../authToken";

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
});
