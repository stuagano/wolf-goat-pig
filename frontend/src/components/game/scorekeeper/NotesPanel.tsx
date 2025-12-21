// =============================================================================
// NotesPanel Component - Live Scorekeeper
// Hole notes input with collapsible UI
// =============================================================================

import React from 'react';
import { useTheme } from '../../../theme/Provider';

interface NotesPanelProps {
  notes: string;
  onSetNotes?: (notes: string) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  isEditable?: boolean;
}

const NotesPanel: React.FC<NotesPanelProps> = ({
  notes,
  onSetNotes,
  isCollapsed = true,
  onToggleCollapse,
  isEditable = true,
}) => {
  const theme = useTheme();
  const hasNotes = notes && notes.trim().length > 0;

  const styles = {
    container: {
      backgroundColor: theme.colors.paper,
      borderRadius: theme.borderRadius.md,
      border: `1px solid ${theme.colors.border}`,
      marginBottom: theme.spacing[4],
      overflow: 'hidden',
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      backgroundColor: theme.colors.gray100,
      cursor: 'pointer',
    },
    headerTitle: {
      fontWeight: theme.typography.semibold,
      fontSize: theme.typography.sm,
      color: theme.colors.textPrimary,
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing[2],
    },
    chevron: {
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
      transition: 'transform 0.2s ease',
      transform: isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)',
    },
    content: {
      padding: theme.spacing[4],
    },
    textarea: {
      width: '100%',
      minHeight: '80px',
      padding: theme.spacing[3],
      fontSize: theme.typography.sm,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.borderRadius.base,
      backgroundColor: theme.colors.inputBackground,
      color: theme.colors.textPrimary,
      resize: 'vertical' as const,
      fontFamily: 'inherit',
    },
    hint: {
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
      marginTop: theme.spacing[2],
    },
    preview: {
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      fontSize: theme.typography.sm,
      color: theme.colors.textPrimary,
      fontStyle: 'italic' as const,
      backgroundColor: theme.colors.gray50,
    },
    emptyPreview: {
      color: theme.colors.textSecondary,
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.header} onClick={onToggleCollapse}>
        <span style={styles.headerTitle}>
          📝 Notes
          {hasNotes && !isCollapsed && (
            <span style={{ fontSize: theme.typography.xs, fontWeight: theme.typography.normal, opacity: 0.7 }}>
              ({notes.length} chars)
            </span>
          )}
        </span>
        <span style={styles.chevron}>▼</span>
      </div>

      {!isCollapsed ? (
        <div style={styles.content}>
          <textarea
            style={styles.textarea}
            value={notes}
            onChange={(e) => onSetNotes?.(e.target.value)}
            placeholder="Add notes about this hole..."
            disabled={!isEditable}
          />
          <div style={styles.hint}>
            Record memorable shots, disputes, or betting drama
          </div>
        </div>
      ) : hasNotes ? (
        <div style={styles.preview}>"{notes}"</div>
      ) : (
        <div style={{ ...styles.preview, ...styles.emptyPreview }}>
          No notes for this hole
        </div>
      )}
    </div>
  );
};

export default NotesPanel;
