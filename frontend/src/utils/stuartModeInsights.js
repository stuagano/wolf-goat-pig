// frontend/src/utils/stuartModeInsights.js

/**
 * Compute how dangerous a player is on a given hole.
 * Lower = more dangerous. Full stroke = 1, Creecher half-stroke = 0.5.
 */
export function computeThreatScore(handicap, strokes) {
  return handicap - strokes;
}

const HIGH_THREAT_CEILING = 4;
const QUARTERS_SWING_THRESHOLD = 3;

/**
 * Generate strategic insights for the authenticated player on the current hole.
 *
 * @param {Object} params
 * @param {Array}  params.players           - All players: { id, name, handicap, is_authenticated }
 * @param {number} params.currentHole       - Hole number (1–18)
 * @param {Object} params.strokeAllocation  - { [playerId]: { [hole]: strokes } }
 * @param {Object} params.playerStandings   - { [playerId]: { quarters } }
 * @param {Object} params.courseData        - { holes: [{ hole_number, handicap }] }
 * @param {number} params.currentWager      - Current wager in quarters
 *
 * @returns {{ headline, detail, threats, soloRecommendation }}
 */
export function generateInsights({
  players,
  currentHole,
  strokeAllocation,
  playerStandings,
  courseData,
  currentWager,
}) {
  const stuart = players.find(p => p.is_authenticated);
  if (!stuart) {
    return {
      headline: 'No authenticated player found',
      detail: '',
      threats: [],
      soloRecommendation: 'caution',
    };
  }

  const strokeIndex = courseData?.holes?.find(h => h.hole_number === currentHole)?.handicap;

  const threats = players.map(player => {
    const strokes = strokeAllocation?.[player.id]?.[currentHole] ?? 0;
    const threatScore = computeThreatScore(player.handicap, strokes);
    const isHighThreat = !player.is_authenticated && threatScore <= HIGH_THREAT_CEILING;
    const quarters = playerStandings?.[player.id]?.quarters ?? 0;
    const hungry = isHighThreat && quarters < -QUARTERS_SWING_THRESHOLD;

    let strokeSituation;
    if (strokes >= 1) strokeSituation = 'full';
    else if (strokes >= 0.4) strokeSituation = 'creecher';
    else strokeSituation = 'none';

    return { player, threatScore, strokeSituation, isHighThreat, hungry, quarters };
  }).sort((a, b) => a.threatScore - b.threatScore);

  const stuartStrokes = strokeAllocation?.[stuart.id]?.[currentHole] ?? 0;
  const stuartQuarters = playerStandings?.[stuart.id]?.quarters ?? 0;
  const highThreats = threats.filter(t => t.isHighThreat);

  let soloRecommendation;
  if (stuartStrokes >= 1 && highThreats.length === 0) {
    soloRecommendation = 'go';
  } else if (stuartStrokes >= 1 && highThreats.length > 0) {
    soloRecommendation = 'caution';
  } else if (stuartStrokes >= 0.4) {
    soloRecommendation = highThreats.length > 0 ? 'caution' : 'go';
  } else {
    soloRecommendation = highThreats.length > 0 ? 'avoid' : 'caution';
  }

  if (stuartQuarters < -QUARTERS_SWING_THRESHOLD) {
    if (soloRecommendation === 'caution') soloRecommendation = 'go';
    else if (soloRecommendation === 'avoid') soloRecommendation = 'caution';
  }

  let headline;
  if (highThreats.length > 0) {
    const names = highThreats.map(t => t.player.name).join(' & ');
    headline = `Watch out for ${names}`;
  } else if (stuartStrokes >= 1) {
    headline = 'Stroke advantage — you have the edge';
  } else if (stuartStrokes >= 0.4 && stuartStrokes < 1) {
    headline = 'Creecher (½ stroke) — partial advantage';
  } else if (strokeIndex && strokeIndex <= 6) {
    headline = `Tough hole (SI ${strokeIndex}) — consider a partner`;
  } else {
    headline = 'Balanced hole — play your read';
  }

  const detailParts = [];

  if (stuartStrokes >= 1) {
    detailParts.push('You get a full stroke here.');
  } else if (stuartStrokes >= 0.4) {
    detailParts.push('You get the Creecher (½ stroke) here.');
  } else {
    detailParts.push('No stroke for you on this hole.');
  }

  highThreats.forEach(t => {
    const strokeNote = t.strokeSituation === 'full'
      ? 'also gets a stroke'
      : t.strokeSituation === 'creecher'
      ? 'gets the Creecher'
      : 'gets no stroke';
    detailParts.push(
      `${t.player.name} is a ${t.player.handicap} hdcp (${strokeNote}) — high threat.`
    );
  });

  if (stuartQuarters < -QUARTERS_SWING_THRESHOLD) {
    detailParts.push(`You're down ${Math.abs(stuartQuarters)}q — higher-variance play makes sense.`);
  } else if (stuartQuarters > QUARTERS_SWING_THRESHOLD) {
    detailParts.push(`You're up ${stuartQuarters}q — a partner reduces risk.`);
  }

  const wagerNote = currentWager > 1 ? ` at ${currentWager}q` : '';
  if (soloRecommendation === 'avoid' && strokeIndex && strokeIndex <= 6) {
    detailParts.push(`Hard hole${wagerNote} — partnership cuts your exposure.`);
  }

  return {
    headline,
    detail: detailParts.join(' '),
    threats,
    soloRecommendation,
  };
}
