const withAlpha = (hex, alpha) => {
  if (!hex || typeof hex !== 'string' || !hex.startsWith('#')) {
    return hex;
  }
  const normalized = hex.replace('#', '');
  if (normalized.length !== 6) {
    return hex;
  }
  const alphaHex = Math.round(Math.min(Math.max(alpha, 0), 1) * 255)
    .toString(16)
    .padStart(2, '0');
  return `#${normalized}${alphaHex}`;
};

const createPanelSurface = (theme, borderColor) => ({
  background: withAlpha(theme.colors.gray900, 0.45),
  padding: theme.spacing[5],
  borderRadius: theme.borderRadius.lg,
  border: `1px solid ${borderColor || withAlpha(theme.colors.paper, 0.12)}`,
  boxShadow: theme.shadows.sm,
});

export const FEEDBACK_PANEL_MAX_HEIGHT = 360;
export const SHOT_META_MIN_WIDTH = 160;

export const createEnhancedSimulationLayoutStyles = (theme) => {
  const { colors, spacing, borderRadius, typography } = theme;

  return {
    container: {
      display: 'grid',
      gridTemplateColumns: '2fr 3fr 2fr',
      gridTemplateRows: 'auto 1fr auto',
      gap: spacing[5],
      padding: spacing[5],
      minHeight: '100vh',
      background: `linear-gradient(135deg, ${colors.primaryDark} 0%, ${colors.primary} 100%)`,
      color: colors.paper,
      fontFamily: typography.fontFamily,
    },
    topBar: {
      gridColumn: '1 / -1',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      background: withAlpha(colors.gray900, 0.5),
      padding: `${spacing[4]} ${spacing[6]}`,
      borderRadius: borderRadius.lg,
      fontSize: typography.base,
      fontWeight: typography.semibold,
    },
    topBarStat: {
      display: 'flex',
      flexDirection: 'column',
      gap: spacing[1],
    },
    topBarLabel: {
      fontSize: typography.xs,
      color: withAlpha(colors.paper, 0.75),
      letterSpacing: '0.08em',
      textTransform: 'uppercase',
    },
    topBarValue: {
      fontSize: typography.base,
      color: colors.paper,
    },
    autoPlayControl: {
      display: 'flex',
      alignItems: 'center',
      gap: spacing[3],
      background: withAlpha(colors.gray900, 0.45),
      padding: `${spacing[2]} ${spacing[4]}`,
      borderRadius: borderRadius.base,
    },
    playNextShotButton: {
      ...theme.createButtonVariant('success'),
      display: 'flex',
      alignItems: 'center',
      gap: spacing[2],
    },
    exportButton: {
      ...theme.createButtonVariant('secondary'),
      fontWeight: typography.semibold,
    },
    pendingBadge: {
      color: colors.warning,
      fontWeight: typography.semibold,
      padding: spacing[2],
      background: withAlpha(colors.warningLight, 0.2),
      borderRadius: borderRadius.base,
    },
    leftPanel: {
      display: 'flex',
      flexDirection: 'column',
      gap: spacing[5],
    },
    centerPanel: {
      display: 'flex',
      flexDirection: 'column',
      gap: spacing[5],
    },
    rightPanel: {
      display: 'flex',
      flexDirection: 'column',
      gap: spacing[5],
    },
    flexGrow: {
      flex: 1,
    },
    playerPanel: {
      ...createPanelSurface(theme, withAlpha(colors.paper, 0.1)),
    },
    panelTitle: {
      margin: 0,
      marginBottom: spacing[4],
      fontSize: typography.lg,
    },
    playerCard: {
      background: withAlpha(colors.paper, 0.12),
      padding: spacing[4],
      borderRadius: borderRadius.base,
      marginBottom: spacing[3],
      border: `1px solid ${withAlpha(colors.paper, 0.25)}`,
      transition: 'border-color 0.2s ease',
    },
    playerCardActive: {
      border: `2px solid ${colors.gold}`,
      background: withAlpha(colors.gold, 0.2),
    },
    playerName: {
      fontSize: typography.lg,
      marginBottom: spacing[2],
    },
    playerMeta: {
      fontSize: typography.sm,
      color: withAlpha(colors.paper, 0.7),
      marginBottom: spacing[2],
    },
    playerPoints: {
      fontSize: typography.base,
      fontWeight: typography.bold,
    },
    metricsPanel: {
      ...createPanelSurface(theme, withAlpha(colors.paper, 0.12)),
    },
    metricSection: {
      marginBottom: spacing[5],
    },
    metricLabel: {
      fontSize: typography.sm,
      marginBottom: spacing[2],
      color: withAlpha(colors.paper, 0.85),
    },
    metricSectionTitle: {
      margin: 0,
      marginBottom: spacing[3],
      fontSize: typography.sm,
      color: withAlpha(colors.paper, 0.85),
      letterSpacing: '0.05em',
      textTransform: 'uppercase',
    },
    metricRow: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: spacing[2],
      fontSize: typography.sm,
      color: withAlpha(colors.paper, 0.9),
    },
    metricValuePositive: {
      color: colors.successLight,
      fontWeight: typography.semibold,
    },
    metricValueNegative: {
      color: colors.errorLight,
      fontWeight: typography.semibold,
    },
    probabilityBar: {
      background: withAlpha(colors.paper, 0.2),
      borderRadius: borderRadius.base,
      height: spacing[5],
      marginBottom: spacing[2],
      overflow: 'hidden',
    },
    probabilityFill: {
      background: `linear-gradient(90deg, ${colors.success} 0%, ${colors.accentLight} 100%)`,
      height: '100%',
      borderRadius: borderRadius.base,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: typography.xs,
      fontWeight: typography.bold,
      color: colors.paper,
    },
    shotDetails: {
      ...createPanelSurface(theme, withAlpha(colors.paper, 0.15)),
    },
    shotPlannerTitle: {
      margin: 0,
      marginBottom: spacing[3],
      fontSize: typography.lg,
      color: colors.paper,
    },
    shotDescription: {
      marginBottom: spacing[4],
      color: withAlpha(colors.paper, 0.85),
      fontSize: typography.base,
      lineHeight: 1.5,
    },
    shotMetaGrid: {
      display: 'grid',
      gridTemplateColumns: `repeat(auto-fit, minmax(${SHOT_META_MIN_WIDTH}px, 1fr))`,
      gap: spacing[3],
    },
    shotMetaItem: {
      background: withAlpha(colors.paper, 0.12),
      padding: spacing[3],
      borderRadius: borderRadius.base,
      border: `1px solid ${withAlpha(colors.paper, 0.2)}`,
    },
    shotMetaLabel: {
      fontSize: typography.xs,
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      color: withAlpha(colors.paper, 0.7),
      marginBottom: spacing[1],
    },
    shotMetaValue: {
      fontSize: typography.base,
      fontWeight: typography.semibold,
      color: colors.paper,
    },
    feedbackPanel: {
      ...createPanelSurface(theme, withAlpha(colors.success, 0.35)),
      maxHeight: FEEDBACK_PANEL_MAX_HEIGHT,
      overflowY: 'auto',
    },
    feedbackItem: {
      marginBottom: spacing[3],
      padding: spacing[3],
      background: withAlpha(colors.paper, 0.08),
      borderRadius: borderRadius.base,
      borderLeft: `4px solid ${colors.success}`,
    },
    feedbackTitle: {
      fontSize: typography.sm,
      fontWeight: typography.semibold,
      marginBottom: spacing[1],
    },
    feedbackBody: {
      fontSize: typography.xs,
      lineHeight: 1.5,
      color: withAlpha(colors.paper, 0.85),
    },
    timelineContainer: {
      ...createPanelSurface(theme, withAlpha(colors.paper, 0.1)),
      padding: 0,
    },
  };
};

export default createEnhancedSimulationLayoutStyles;
