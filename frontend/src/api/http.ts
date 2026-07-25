/**
 * Small helpers for working with the typed API client (`src/api/client`).
 */

/**
 * Extract a human-readable message from a FastAPI error body.
 *
 * FastAPI errors come back as `{ detail: string | ValidationError[] }`; this
 * returns the string form and `undefined` for the array/500 cases so callers
 * can fall back to their own message.
 */
export function errorDetail(error: unknown): string | undefined {
  if (error && typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === 'string') return detail;
  }
  return undefined;
}
