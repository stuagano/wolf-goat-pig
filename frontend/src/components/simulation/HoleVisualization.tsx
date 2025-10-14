// @ts-nocheck
import React, { useMemo } from 'react';
import { useTheme } from '../../theme/Provider';

type Player = {
  id: string;
  name: string;
  handicap?: number;
  is_human?: boolean;
  status?: string;
};

type BallPosition = {
  distance_to_pin?: number | null;
  lie?: string | null;
  last_shot?: {
    club?: string | null;
    result?: string | null;
  } | null;
};

type HoleVisualizationProps = {
  holeDistance?: number | null;
  par?: number | null;
  holeNumber?: number | null;
  players?: Player[];
  ballPositions?: Record<string, BallPosition | undefined> | null;
  nextPlayerId?: string | null;
  currentShotNumber?: number | null;
};

const DEFAULT_HOLE_DISTANCE = 400;

const clamp = (value: number, min: number, max: number) => {
  if (Number.isNaN(value)) {
    return min;
  }
  return Math.min(Math.max(value, min), max);
};

const yardsLabel = (value?: number | null) => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return null;
  }
  return `${Math.round(value)} yds`;
};

const HoleVisualization: React.FC<HoleVisualizationProps> = ({
  holeDistance,
  par,
  holeNumber,
  players = [],
  ballPositions = {},
  nextPlayerId,
  currentShotNumber,
}) => {
  const theme = useTheme();
  const { colors, spacing, borderRadius, shadows, typography } = theme;

  const effectiveHoleDistance = useMemo(() => {
    if (typeof holeDistance === 'number' && holeDistance > 0) {
      return holeDistance;
    }
    return DEFAULT_HOLE_DISTANCE;
  }, [holeDistance]);

  const playerMarkers = useMemo(() => {
    const records = players.map((player, index) => {
      const ball = ballPositions?.[player.id];
      const distanceToPin = typeof ball?.distance_to_pin === 'number' ? ball.distance_to_pin : null;
      const progress = distanceToPin === null
        ? 0
        : clamp((effectiveHoleDistance - distanceToPin) / effectiveHoleDistance, 0, 1);

      return {
        player,
        ball,
        distanceToPin,
        progress,
        rowIndex: index,
      };
    });

    return records;
  }, [players, ballPositions, effectiveHoleDistance]);

  const hasMarkers = playerMarkers.length > 0;

  const nextMarker = useMemo(() => {
    if (!nextPlayerId) {
      return null;
    }
    return playerMarkers.find((marker) => marker.player.id === nextPlayerId) || null;
  }, [nextPlayerId, playerMarkers]);

  const lineOfScrimmageProgress = useMemo(() => {
    if (nextMarker) {
      return nextMarker.progress;
    }
    const furthest = playerMarkers.reduce((max, marker) => Math.max(max, marker.progress), 0);
    return furthest;
  }, [nextMarker, playerMarkers]);

  const laneHeight = 56;
  const verticalPadding = 48;
  const trackHeight = Math.max(playerMarkers.length * laneHeight + verticalPadding, 260);

  const renderMarker = (marker: typeof playerMarkers[number]) => {
    const { player, ball, distanceToPin, progress, rowIndex } = marker;
    const safeProgress = clamp(progress, 0.02, 0.98);
    const leftPosition = `${safeProgress * 100}%`;
    const topPosition = 32 + rowIndex * laneHeight;
    const isNext = nextPlayerId === player.id;
    const icon = player.id === 'human' || player.is_human ? '👤' : '🤖';

    return (
      <div
        key={player.id}
        style={{
          position: 'absolute',
          left: leftPosition,
          top: topPosition,
          transform: 'translate(-50%, -50%)',
          minWidth: 140,
          background: isNext ? colors.accent : 'rgba(0, 0, 0, 0.6)',
          color: '#fff',
          padding: spacing[3],
          borderRadius: borderRadius.md,
          boxShadow: shadows.md,
          border: `1px solid ${isNext ? colors.accentLight : 'rgba(255,255,255,0.3)'}`,
          transition: 'transform 0.2s ease, box-shadow 0.2s ease',
          fontFamily: typography.fontFamily,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing[2], marginBottom: spacing[1] }}>
          <span style={{ fontSize: typography.lg }}>{icon}</span>
          <span style={{ fontSize: typography.sm, fontWeight: typography.semibold }}>{player.name}</span>
        </div>
        {distanceToPin !== null ? (
          <div style={{ fontSize: typography.xs, opacity: 0.85 }}>
            {yardsLabel(distanceToPin)} to pin
          </div>
        ) : (
          <div style={{ fontSize: typography.xs, opacity: 0.65 }}>Awaiting shot data</div>
        )}
        {ball?.lie && (
          <div style={{ fontSize: typography.xs, opacity: 0.7 }}>
            Lie: {ball.lie}
          </div>
        )}
        {ball?.last_shot?.result && (
          <div style={{ fontSize: typography.xs, opacity: 0.6 }}>
            Last: {ball.last_shot.result}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      style={{
        background: `linear-gradient(135deg, ${colors.primaryDark} 0%, ${colors.primary} 40%, ${colors.fairway} 100%)`,
        borderRadius: borderRadius.lg,
        padding: spacing[5],
        border: `2px solid rgba(255, 255, 255, 0.12)`,
        color: '#fff',
        boxShadow: shadows.lg,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: spacing[4],
          fontFamily: typography.fontFamily,
        }}
      >
        <div>
          <div style={{ fontSize: typography.sm, textTransform: 'uppercase', opacity: 0.7 }}>
            {holeNumber ? `Hole ${holeNumber}` : 'Hole Overview'}
          </div>
          <div style={{ fontSize: typography['2xl'], fontWeight: typography.bold }}>
            {yardsLabel(effectiveHoleDistance)} • Par {par ?? '—'}
          </div>
          {typeof currentShotNumber === 'number' && (
            <div style={{ fontSize: typography.xs, opacity: 0.7 }}>Current Shot #{currentShotNumber}</div>
          )}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: spacing[3],
            fontSize: typography.sm,
            background: 'rgba(0, 0, 0, 0.3)',
            padding: `${spacing[2]} ${spacing[3]}`,
            borderRadius: borderRadius.base,
          }}
        >
          <span role="img" aria-label="tee">🏁</span>
          <span style={{ opacity: 0.8 }}>Tee Box → Green</span>
          <span role="img" aria-label="green flag">🚩</span>
        </div>
      </div>

      <div
        style={{
          position: 'relative',
          height: trackHeight,
          background: 'rgba(0, 0, 0, 0.35)',
          borderRadius: borderRadius.md,
          border: '1px solid rgba(255,255,255,0.2)',
          overflow: 'hidden',
        }}
      >
        {hasMarkers && (
          <div
            style={{
              position: 'absolute',
              top: spacing[3],
              left: spacing[3],
              display: 'flex',
              flexDirection: 'column',
              gap: spacing[2],
              color: 'rgba(255,255,255,0.7)',
              fontSize: typography.xs,
              fontFamily: typography.fontFamily,
            }}
          >
            {playerMarkers.map((marker) => (
              <div key={`label-${marker.player.id}`} style={{ display: 'flex', alignItems: 'center', gap: spacing[2] }}>
                <div
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: marker.player.id === nextPlayerId ? colors.accentLight : '#fff',
                  }}
                />
                <span>{marker.player.name}</span>
              </div>
            ))}
          </div>
        )}

        {/* Fairway path */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: '50%',
            height: 36,
            background: `linear-gradient(90deg, ${colors.sandTrap} 0%, rgba(255,255,255,0.85) 12%, ${colors.fairway} 45%, ${colors.primaryLight} 100%)`,
            transform: 'translateY(-50%)',
            borderTop: '1px solid rgba(255,255,255,0.3)',
            borderBottom: '1px solid rgba(0,0,0,0.2)',
          }}
        />

        {/* Tee marker */}
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: spacing[4],
            transform: 'translateY(-50%)',
            textAlign: 'center',
            color: '#fff',
            fontFamily: typography.fontFamily,
          }}
        >
          <div style={{ fontSize: typography.lg }}>🏁</div>
          <div style={{ fontSize: typography.xs, opacity: 0.7 }}>Tee Box</div>
        </div>

        {/* Green marker */}
        <div
          style={{
            position: 'absolute',
            top: '50%',
            right: spacing[4],
            transform: 'translateY(-50%)',
            textAlign: 'center',
            color: '#fff',
            fontFamily: typography.fontFamily,
          }}
        >
          <div style={{ fontSize: typography.lg }}>🚩</div>
          <div style={{ fontSize: typography.xs, opacity: 0.7 }}>Green</div>
        </div>

        {/* Line of scrimmage */}
        {hasMarkers ? (
          <>
            <div
              style={{
                position: 'absolute',
                top: 0,
                bottom: 0,
                left: `${clamp(lineOfScrimmageProgress, 0.02, 0.98) * 100}%`,
                transform: 'translateX(-50%)',
                width: 2,
                background: colors.accentLight,
                boxShadow: `0 0 12px ${colors.accentLight}`,
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  top: spacing[2],
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: colors.accent,
                  padding: `${spacing[1]} ${spacing[2]}`,
                  borderRadius: borderRadius.base,
                  fontSize: typography.xs,
                  fontFamily: typography.fontFamily,
                  whiteSpace: 'nowrap',
                  boxShadow: shadows.sm,
                }}
              >
                Line of Scrimmage
              </div>
            </div>

            {playerMarkers.map(renderMarker)}
          </>
        ) : (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              color: 'rgba(255,255,255,0.75)',
              fontSize: typography.sm,
              fontFamily: typography.fontFamily,
            }}
          >
            Shot data will appear here once the hole begins.
          </div>
        )}
      </div>
    </div>
  );
};

export default HoleVisualization;
