import React from 'react';
import { Link } from 'react-router-dom';

export default function PlayerName({ name, playerId, className = '' }) {
  const label = name || 'Unknown Player';
  if (!playerId) return <span className={className}>{label}</span>;
  return (
    <Link to={`/players/${playerId}`} className={`hover:text-blue-600 hover:underline ${className}`}>
      {label}
    </Link>
  );
}
