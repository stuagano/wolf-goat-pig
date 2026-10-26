import React, { useEffect, useRef, useState } from 'react';
import { apiConfig } from '../../config/api.config';
import { preprocessScorecardImage } from '../../utils/scorecardImage';
import { initialMapping, savedBalances, comparisonRows } from './cardExtractionComparison';
import './CardExtractionValidation.css';

/** No save callback by design: extraction is independent evidence, never an edit. */
export default function CardExtractionValidation(props) {
  // A different photo or roster must never inherit an in-flight scan or mapping.
  return <ValidationSession key={JSON.stringify([props.photoSrc, props.players])} {...props} />;
}

function ValidationSession({ photoSrc, players, holeHistory = [] }) {
  const [result, setResult] = useState(null);
  const [mapping, setMapping] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);

  const scan = async () => {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const photo = await fetch(photoSrc, { signal: controller.signal, cache: 'no-store' });
      if (!photo.ok) throw new Error(`Could not read saved photo (${photo.status}). Retry the photo first.`);
      const blob = await photo.blob();
      const file = await preprocessScorecardImage(new File([blob], 'saved-card.jpg', { type: blob.type }));
      if (controller.signal.aborted) return;
      const body = new FormData();
      body.append('file', file);
      const response = await fetch(`${apiConfig.baseUrl}/scorecard/scan`, { method: 'POST', body, signal: controller.signal });
      if (!response.ok) throw new Error(`Extraction failed (${response.status}). Please try again.`);
      const data = await response.json();
      if (!data || !Array.isArray(data.players) || !Array.isArray(data.running_totals)) throw new Error('The scanner returned an unreadable result. Please try again.');
      if (controller.signal.aborted) return;
      setMapping(initialMapping(data.players, players));
      setResult(data);
    } catch (err) {
      if (!controller.signal.aborted) setError(err.message || 'Extraction failed. Please try again.');
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  };

  return (
    <section className="card-validation" aria-label="Extraction validation">
      <h3>Check extraction against saved scores</h3>
      <p>Saved scores are the ground truth. Differences are possible extraction errors, not corrections. This check never changes scores.</p>
      <button type="button" disabled={busy} onClick={scan}>{busy ? 'Extracting card…' : result || error ? 'Retry extraction' : 'Extract & compare card'}</button>
      {busy && <>
        <button type="button" onClick={() => { request.current?.abort(); setBusy(false); }}>Cancel extraction</button>
        <p role="status">Reading the saved photo. Scores remain unchanged.</p>
      </>}
      {error && <p role="alert">{error}</p>}
      {result && <>
        <p>Running quarters after each hole: saved per-hole quarters added together, compared with the raw card reading. Strokes are not compared. Low or unknown confidence is marked uncertain.</p>
        {result.players.length === 0 && <p role="status">No players were extracted. Try another extraction or inspect the photo.</p>}
        {players.filter((_, i) => !mapping.includes(String(i))).map((p, i) => <p key={i}>Not compared: {p.name} — no mapped extraction.</p>)}
        {result.players.map((entry, index) => {
          const selected = mapping[index];
          const player = selected !== '' ? players[Number(selected)] : null;
          const duplicate = selected !== '' && mapping.filter(m => m === selected).length > 1;
          const balances = player ? savedBalances(holeHistory, player.id) : [];
          // Totals-only imports store zeros on 1–17. There is no provenance flag;
          // do not label those intermediate placeholders as extraction errors.
          const possibleTotalsOnly = balances.length === 18 && balances.slice(0, 17).every(v => v === 0) && balances[17] !== null;
          const rows = player ? comparisonRows(result.running_totals, index, balances).filter(row => !possibleTotalsOnly || row.hole === 18) : [];
          return <div className="card-validation__player" key={index}>
            <label>
              Card row {index + 1}: {typeof entry?.name === 'string' && entry.name.trim() ? entry.name : 'Unreadable name'} → recorded player
              <select aria-label={`Map card row ${index + 1}`} value={selected} onChange={e => setMapping(prev => prev.map((m, i) => i === index ? e.target.value : m))}>
                <option value="">Choose player — not compared</option>
                {players.map((p, i) => <option key={i} value={i}>{p.name} ({p.id})</option>)}
              </select>
            </label>
            {!player && <p>Player mapping uncertain or missing. Choose explicitly; row order is never used.</p>}
            {duplicate && <p role="alert">Ambiguous mapping: more than one card row is assigned to {player?.name}. Choose distinct players before comparing.</p>}
            {player && !duplicate && possibleTotalsOnly && <p>Saved history may contain only a final total. Comparing hole 18 only; intermediate quarters are not verified.</p>}
            {player && !duplicate && <table aria-label={`${player.name} running quarters`}>
              <caption>{player.name} · running quarters</caption>
              <thead><tr><th scope="col">Hole</th><th scope="col">Saved</th><th scope="col">Extracted</th><th scope="col">Check</th></tr></thead>
              <tbody>{rows.map(row => <tr key={row.hole} className={row.status === 'Possible extraction error' ? 'card-validation__mismatch' : ''}>
                <th scope="row">{row.hole}</th><td>{row.saved ?? '—'}</td><td>{row.extracted ?? '—'}</td><td>{row.status}{row.uncertain && row.status === 'Possible extraction error' ? ' · uncertain' : ''}</td>
              </tr>)}</tbody>
            </table>}
          </div>;
        })}
      </>}
    </section>
  );
}
