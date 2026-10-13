// Every `theme.colors.X` used in components must exist in BOTH real palettes.
// Test mocks define extra keys (e.g. backgroundSecondary), which hid that the
// real theme lacked one: the scorekeeper's sticky status pill rendered with no
// background and its text bled over the player rows.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { lightColors, darkColors } from '../theme';

const SRC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

// Pre-existing gaps (mostly text colors, which just inherit). Ratchet: remove
// entries as they're fixed; never add new ones.
const KNOWN_MISSING = new Set([
  'cardBackground', 'danger', 'errorBg', 'primaryContrast',
  'secondary', 'successBg', 'surface', 'text',
]);

function usedColorKeys(dir, keys = new Set()) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!['__tests__', 'test-utils'].includes(entry.name)) usedColorKeys(full, keys);
    } else if (/\.(jsx?|tsx?)$/.test(entry.name) && !/\.test\./.test(entry.name)) {
      for (const [, key] of fs.readFileSync(full, 'utf8').matchAll(/theme\.colors\.(\w+)/g)) keys.add(key);
    }
  }
  return keys;
}

test.each([['light', lightColors], ['dark', darkColors]])(
  'every theme.colors key used in src exists in the %s palette',
  (_, palette) => {
    const missing = [...usedColorKeys(SRC)].filter((key) => !(key in palette) && !KNOWN_MISSING.has(key));
    expect(missing).toEqual([]);
  },
);
