import * as Sentry from "@sentry/react";

// No-op unless VITE_SENTRY_DSN is set (dev/preview without the env are clean).
export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  if (!dsn) return false;
  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0,
    sendDefaultPii: false,
  });
  return true;
}

export function captureException(error) {
  Sentry.captureException(error);
}
