import React from 'react';
import { Link } from 'react-router-dom';

export default function PlayerName({ name, playerId, className = '' }) {
  const label = name || 'Unknown Player';
  if (!name && !playerId) return <span className={className}>{label}</span>;
  // Sheet-only players have no id; the name route shows their recorded rounds.
  const to = playerId ? `/players/${playerId}` : `/players/name/${encodeURIComponent(name)}`;
  return (
    <Link to={to} className={`hover:text-blue-600 hover:underline ${className}`}>
      {label}
    </Link>
  );
}
