/**
 * Quarters input helpers.
 *
 * Quarters are wager deltas: they can be positive, negative, or fractional
 * (e.g. 0.5). On a mobile numeric keypad there's no minus sign, so the UI
 * relies on +/- steppers and a sign-flip (±) button, and the text inputs
 * accept in-progress strings like "-", "." or "1." while the user types.
 *
 * Without these helpers those partial strings silently became 0 on submit
 * (parseFloat("-") === NaN, then `NaN || 0`), which produced a confusing
 * "Quarters must sum to zero" error even when entries looked balanced.
 */

/**
 * Parse a raw quarters value to a finite number, or null if it isn't a
 * complete number yet. Treats "", "-", ".", "-." and similar in-progress /
 * malformed strings as null (not 0), so callers can tell "not entered yet"
 * apart from "entered as zero".
 *
 * @param {string|number|null|undefined} raw
 * @returns {number|null}
 */
export function parseQuarter(raw) {
  if (raw === undefined || raw === null || raw === "") return null;
  const n = typeof raw === "number" ? raw : parseFloat(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Normalize a raw input string to a clean canonical form for display/storage.
 * Finite numbers collapse to their shortest string ("1." -> "1", "-0" -> "0");
 * anything that isn't a complete number yet collapses to "" so the field shows
 * its placeholder instead of leaving a dangling "-" or ".".
 *
 * Intended for use on blur, so it never fights the user mid-keystroke.
 *
 * @param {string|number|null|undefined} raw
 * @returns {string}
 */
export function normalizeQuarterInput(raw) {
  const n = parseQuarter(raw);
  if (n === null) return "";
  // Collapse -0 to 0 and drop trailing ".".
  return String(n === 0 ? 0 : n);
}

/**
 * Flip the sign of a raw quarters value for a sign-toggle button.
 *
 * Crucially handles the empty/zero case by "arming" a negative ("" -> "-"),
 * so the user can tap the sign FIRST and then type the magnitude on a numeric
 * keypad that has no minus key. Idempotent toggle: tapping again disarms it.
 *
 *   ""  -> "-"      "-"   -> ""       "0" -> "-"
 *   "3" -> "-3"     "-3"  -> "3"      "0.5" -> "-0.5"
 *
 * @param {string|number|null|undefined} raw
 * @returns {string}
 */
export function flipSign(raw) {
  const s = raw === undefined || raw === null ? "" : String(raw).trim();
  if (s === "" || s === "0") return "-";
  if (s === "-") return "";
  if (s.startsWith("-")) {
    const rest = s.slice(1);
    return rest === "0" ? "" : rest;
  }
  return "-" + s;
}

/**
 * True when a raw value is negative or "armed" negative ("-"). Drives the
 * red styling / "−" label on the sign-toggle button.
 *
 * @param {string|number|null|undefined} raw
 * @returns {boolean}
 */
export function isNegativeInput(raw) {
  if (typeof raw === "number") return raw < 0;
  return String(raw ?? "").trim().startsWith("-");
}
