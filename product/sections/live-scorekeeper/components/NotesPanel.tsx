// =============================================================================
// NotesPanel Component - Live Scorekeeper
// Hole notes input with collapsible UI
// =============================================================================

import React from 'react';

interface NotesPanelProps {
  notes: string;
  onSetNotes?: (notes: string) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  isEditable?: boolean;
}

const styles = {
  container: {
    backgroundColor: 'var(--color-paper, #ffffff)',
    borderRadius: '12px',
    border: '1px solid var(--color-border, #e0e0e0)',
    marginBottom: '16px',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    backgroundColor: 'var(--color-gray-100, #f5f5f5)',
    cursor: 'pointer',
  },
  headerTitle: {
    fontWeight: 600,
    fontSize: '14px',
    color: 'var(--color-text-primary, #212121)',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  chevron: {
    fontSize: '12px',
    color: 'var(--color-text-secondary, #757575)',
    transition: 'transform 0.2s ease',
  },
  content: {
    padding: '16px',
  },
  textarea: {
    width: '100%',
    minHeight: '80px',
    padding: '12px',
    fontSize: '14px',
    border: '1px solid var(--color-border, #e0e0e0)',
    borderRadius: '8px',
    backgroundColor: 'var(--color-input-bg, #ffffff)',
    color: 'var(--color-text-primary, #212121)',
    resize: 'vertical' as const,
    fontFamily: 'inherit',
  },
  hint: {
    fontSize: '12px',
    color: 'var(--color-text-secondary, #757575)',
    marginTop: '8px',
  },
  preview: {
    padding: '12px 16px',
    fontSize: '14px',
    color: 'var(--color-text-primary, #212121)',
    fontStyle: 'italic' as const,
    backgroundColor: 'var(--color-gray-50, #fafafa)',
  },
  emptyPreview: {
    color: 'var(--color-text-secondary, #757575)',
  },
};

const NotesPanel: React.FC<NotesPanelProps> = ({
  notes,
  onSetNotes,
  isCollapsed = true,
  onToggleCollapse,
  isEditable = true,
}) => {
  const hasNotes = notes && notes.trim().length > 0;

  return (
    <div style={styles.container}>
      <div style={styles.header} onClick={onToggleCollapse}>
        <span style={styles.headerTitle}>
          \u{1F4DD} Notes
          {hasNotes && !isCollapsed && (
            <span style={{ fontSize: '12px', fontWeight: 400, opacity: 0.7 }}>
              ({notes.length} chars)
            </span>
          )}
        </span>
        <span
          style={{
            ...styles.chevron,
            transform: isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)',
          }}
        >
          \u25BC
        </span>
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
