// frontend/src/components/simulation/visual/PlayersCard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Card } from '../../ui';
import { useTheme } from '../../../theme/Provider';

const PlayersCard = ({ players = [], captainId = null }) => {
  const theme = useTheme();

  return (
    <Card style={{ height: '100%' }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
        PLAYERS
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {players.map(player => {
          const isCaptain = player.id === captainId;
          const isHuman = player.is_human || player.id === 'human';

          return (
            <div
              key={player.id}
              data-is-human={isHuman}
              style={{
                padding: theme.spacing[2],
                borderRadius: theme.borderRadius.sm,
                backgroundColor: isHuman ? 'rgba(33, 150, 243, 0.1)' : 'transparent',
                border: isHuman ? '1px solid rgba(33, 150, 243, 0.3)' : '1px solid transparent'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
                  <span style={{ fontSize: '20px', flexShrink: 0 }}>
                    {isHuman ? '👤' : '🤖'}
                  </span>
                  <span style={{ fontWeight: isHuman ? 'bold' : 'normal', wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                    {player.name}
                    {isCaptain && ' 👑'}
                  </span>
                </div>
                <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
                  Points: <span style={{ fontWeight: 'bold', fontSize: '16px' }}>
                    {player.points || 0}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

PlayersCard.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    points: PropTypes.number,
    is_human: PropTypes.bool
  })),
  captainId: PropTypes.string
};

export default PlayersCard;
