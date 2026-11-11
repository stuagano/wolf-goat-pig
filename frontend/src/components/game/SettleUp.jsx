import React, { useEffect, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { apiConfig } from '../../config/api.config';
import { settleUp, venmoPayUrl } from '../../utils/settleUp';

const money = dollars => `$${dollars.toFixed(2)}`;

/** Who pays whom for one finished round, with one-tap Venmo links. */
export default function SettleUp({ players, note }) {
  const [handles, setHandles] = useState({});
  const { balanced, payments } = useMemo(() => settleUp(players), [players]);

  useEffect(() => {
    if (!balanced || !payments.length) return undefined;
    let cancelled = false;
    // Public list already carries venmo_handle; cached 60s server-side.
    fetch(`${apiConfig.baseUrl}/players`)
      .then(res => (res.ok ? res.json() : []))
      .then(list => {
        if (!cancelled) setHandles(Object.fromEntries(list.filter(p => p.venmo_handle).map(p => [p.id, p.venmo_handle])));
      })
      .catch(() => {}); // Without handles the list still shows who owes whom.
    return () => { cancelled = true; };
  }, [balanced, payments.length]);

  if (!balanced) {
    return (
      <section aria-label="Settle up">
        <h2>Settle up</h2>
        <p role="status">Quarters don&apos;t balance — fix the card first.</p>
      </section>
    );
  }
  if (!payments.length) return null;

  return (
    <section aria-label="Settle up">
      <h2>Settle up</h2>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {payments.map(({ from, to, dollars }) => {
          const handle = to.profile_id != null ? handles[to.profile_id] : null;
          const who = `${from.name || 'Player'} pays ${to.name || 'Player'} ${money(dollars)}`;
          return (
            <li key={`${from.id}-${to.id}`} style={{ marginBottom: 8 }}>
              <span>{who}</span>{' '}
              {handle ? (
                <a href={venmoPayUrl(handle, dollars, note)} target="_blank" rel="noopener noreferrer">
                  Pay on Venmo
                </a>
              ) : (
                <span style={{ color: '#6b7280', fontSize: 13 }}>({to.name || 'Player'} has no Venmo yet)</span>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

SettleUp.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    profile_id: PropTypes.number,
    quarters: PropTypes.number,
  })).isRequired,
  note: PropTypes.string.isRequired,
};
