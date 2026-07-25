import createClient from 'openapi-fetch';
import type { paths } from './schema';
import { apiConfig } from '../config/api.config';

/**
 * Typed API client generated against the backend OpenAPI contract.
 *
 * Source of truth: `backend/openapi.json` → `src/api/schema.d.ts`
 * (regenerate both with `npm run gen:api`). Every request path, path/query
 * param, request body, and response is checked against the spec at compile
 * time — the frontend is a thin, typed consumer of the backend contract.
 *
 * Auth is per-request: callers pass `headers: { Authorization: 'Bearer <token>' }`
 * with a token acquired via Auth0 (`acquireAccessToken`). Keeping auth out of the
 * client leaves it stateless and trivially testable.
 */
export const api = createClient<paths>({
  baseUrl: apiConfig.baseUrl,
  // Resolve `fetch` per request rather than capturing globalThis.fetch at client
  // creation. This keeps prod behavior identical while letting tests that swap
  // `global.fetch` (after this module is imported) intercept the client's calls.
  fetch: (input: Request) => globalThis.fetch(input),
});

export default api;
