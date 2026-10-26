// Local-only fixture API for agent-browser review. Never proxies to a real API.
// Run: node frontend/tests/e2e/fixtures/round-card-review-server.mjs
import http from 'node:http';

const players = ['Alice', 'Bob', 'Charlie', 'Diana'].map((name, i) => ({ id: `p${i + 1}`, name, handicap: 0 }));
const initial = () => ({
  players, current_hole: 19, game_status: 'completed', course_name: 'Review Course', base_wager: 1,
  hole_history: Array.from({ length: 18 }, (_, i) => ({ hole: i + 1, gross_scores: { p1: 4, p2: 5, p3: 4, p4: 5 }, points_delta: { p1: 1, p2: -1, p3: 1, p4: -1 }, wager: 1 })),
});
let state = initial();
let lastSave = null;
let scans = [];
const extraction = {
  players: players.map(p => ({ name: p.name, confidence: 1 })),
  running_totals: players.flatMap((p, pi) => Array.from({ length: 18 }, (_, i) => ({
    player_index: pi, hole: i + 1, value: (pi % 2 ? -1 : 1) * (i + 1) + (pi === 0 && i === 1 ? 3 : 0), confidence: i === 2 ? 0.4 : 1,
  }))).filter(t => !(t.player_index === 1 && t.hole === 4)),
};
const photo = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800"><rect width="1200" height="800" fill="#f7f1df"/><text x="40" y="65" font-size="36" fill="#234b32">REVIEW COURSE · PAPER SCORECARD (test fixture)</text>${players.map((p, i) => `<text x="40" y="${160 + i * 120}" font-size="28">${p.name}   4   5   4   5   4   5   4   5   4   |   40</text><path d="M30 ${190 + i * 120} H1170" stroke="#527b63"/>`).join('')}</svg>`;

http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS');
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') { res.writeHead(204); return res.end(); }
  const url = new URL(req.url, 'http://localhost');
  const path = url.pathname;
  const json = (data, status = 200) => { res.writeHead(status, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(data)); };
  if (path === '/fixture/reset') { state = initial(); lastSave = null; scans = []; return json({ ok: true }); }
  if (path === '/fixture/evidence') return json({ state, lastSave, scans });
  if (path === '/scorecard/scan' && req.method === 'POST') {
    const chunks = []; for await (const chunk of req) chunks.push(chunk);
    const body = Buffer.concat(chunks).toString();
    const fields = [...body.matchAll(/; name="([^"]+)"/g)].map(m => m[1]);
    scans.push({ fields, bytes: Buffer.byteLength(body) });
    if (fields.length !== 1 || fields[0] !== 'file') return json({ detail: 'Only the photo is permitted' }, 422);
    return json(extraction);
  }
  if (path.endsWith('/state')) return json(state);
  if (path.endsWith('/card')) return json({ can_edit: !path.includes('readonly'), has_photo: true });
  if (path.endsWith('/scorecard-photo')) {
    if (path.includes('missing')) return json({ detail: 'No photo' }, 404);
    if (path.includes('error')) return json({ detail: 'Unavailable' }, 503);
    res.writeHead(200, { 'Content-Type': 'image/svg+xml' }); return res.end(photo);
  }
  if (path.endsWith('/scores') && req.method === 'POST') {
    let body = ''; for await (const chunk of req) body += chunk;
    lastSave = JSON.parse(body);
    if (!Array.isArray(lastSave.holes) || lastSave.current_hole !== 19) return json({ detail: 'Expected completed-round score payload' }, 422);
    state.hole_history = lastSave.holes.map(({ hole_number, quarters, ...details }) => ({ ...details, hole: hole_number, points_delta: quarters }));
    return json({ success: true });
  }
  if (path === '/players/me') return json({ id: 1, name: 'Alice', legacy_name: 'Alice' });
  if (path === '/courses') return json({ 'Review Course': { holes: Array.from({ length: 18 }, (_, i) => ({ hole_number: i + 1, par: 4, handicap: i + 1 })) } });
  if (path.includes('/rotation/')) return json({ rotation_order: players.map(p => p.id), captain_index: 0, current_wager: 1 });
  if (path === '/legacy-players') return json({ players: players.map(p => p.name) });
  if (path.includes('/notifications')) return json([]);
  return json({});
}).listen(8334, '127.0.0.1', () => process.stdout.write('Review fixture API: http://127.0.0.1:8334\n'));
