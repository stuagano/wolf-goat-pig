// Stuart Mode score simulation. Generates plausible gross strokes for
// AI / absent players when Stuart is playing solo, so the hole math has
// numbers to work with. Deterministic per (gameId, hole, player) so a
// re-render returns the same value, but each round (different gameId)
// rolls different scores.

const mulberry32 = (seed) => {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

const hashString = (str) => {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
};

const standardNormal = (rand) => {
  // Box–Muller, two uniforms → one normal sample.
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
};

export const simulatePlayerScore = ({
  player,
  par,
  strokeIndex,
  gameId,
  hole,
}) => {
  const seed =
    hashString(`${gameId || "no-game"}|${player.id}|${hole}`) ^
    (hole * 0x9e3779b1);
  const rand = mulberry32(seed);

  const handicap = Math.max(0, Number(player.handicap) || 18);
  const par4 = Number(par) || 4;

  // Expected over-par rises with handicap and difficulty (low stroke index = hard).
  // Calibration: 12-handicap on an SI-9 par 4 should hover near bogey.
  const difficulty = strokeIndex
    ? (19 - strokeIndex) / 18 // SI 1 → ~1.0, SI 18 → ~0.06
    : 0.5;
  const expectedOver = (handicap / 18) + difficulty * 0.6;

  const noise = standardNormal(rand) * 1.0;
  const raw = par4 + expectedOver + noise;
  const rounded = Math.round(raw);

  // Clamp to a sane band: at best a birdie, at worst quad bogey.
  return Math.max(par4 - 1, Math.min(par4 + 4, rounded));
};

export const prefillAiScores = ({
  players,
  currentScores,
  par,
  strokeIndex,
  gameId,
  hole,
}) => {
  const filled = { ...currentScores };
  for (const p of players) {
    // Skip the authenticated user (Stuart) and anyone with a score already.
    if (p.is_authenticated) continue;
    if (filled[p.id]) continue;
    filled[p.id] = simulatePlayerScore({ player: p, par, strokeIndex, gameId, hole });
  }
  return filled;
};
