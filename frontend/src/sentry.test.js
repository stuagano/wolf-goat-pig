import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@sentry/react", () => ({ init: vi.fn(), captureException: vi.fn() }));
import * as Sentry from "@sentry/react";
import { initSentry } from "./sentry";

describe("initSentry", () => {
  beforeEach(() => vi.clearAllMocks());

  it("is a no-op when VITE_SENTRY_DSN is not set", () => {
    vi.stubEnv("VITE_SENTRY_DSN", "");
    expect(initSentry()).toBe(false);
    expect(Sentry.init).not.toHaveBeenCalled();
    vi.unstubAllEnvs();
  });

  it("initializes when VITE_SENTRY_DSN is set", () => {
    vi.stubEnv("VITE_SENTRY_DSN", "https://k@o1.ingest.sentry.io/1");
    expect(initSentry()).toBe(true);
    expect(Sentry.init).toHaveBeenCalledOnce();
    vi.unstubAllEnvs();
  });
});
