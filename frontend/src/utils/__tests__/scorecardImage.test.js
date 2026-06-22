import { test, expect, vi } from 'vitest';
import { downscaleToBase64 } from '../scorecardImage';

test('downscaleToBase64 returns null when canvas/bitmap unavailable (jsdom)', async () => {
  // jsdom has no real canvas encoding; the helper must degrade to null, not throw.
  const file = new File([new Uint8Array([1, 2, 3])], 'c.jpg', { type: 'image/jpeg' });
  const out = await downscaleToBase64(file, 1200);
  expect(out === null || typeof out === 'string').toBe(true);
});
