import React from 'react';
import { useTheme } from '../../theme/Provider';

const KIND_LABELS = {
  submit: 'Confirm final submit',
  safety: 'Safety confirmation required',
};

/**
 * Mid-flow confirmation for the Computer Use booking agent.
 * Shown for the final submit/cancel and Google safety gates. Login is not
 * gated — the agent fills credentials server-side, and a pause there let
 * Cloud Run scale the instance (and the job's browser) away mid-flow.
 */
const AgentConfirmDialog = ({ pendingConfirm, onResolve }) => {
  const theme = useTheme();
  if (!pendingConfirm) return null;

  const confirmKind = pendingConfirm.kind || 'safety';
  const confirmTitle = KIND_LABELS[confirmKind] || KIND_LABELS.safety;

  return (
    <>
      <div
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.5)',
          zIndex: 2100,
        }}
      />
      <div
        role="dialog"
        aria-modal="true"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 2101,
          ...theme.cardStyle,
          padding: 24,
          minWidth: 320,
          maxWidth: 420,
          width: '90vw',
        }}
      >
        <h3 style={{ color: theme.colors.primary, margin: '0 0 12px' }}>
          {confirmTitle}
        </h3>
        <p style={{ margin: '0 0 16px', color: theme.colors.textPrimary, fontSize: 14, lineHeight: 1.45 }}>
          {pendingConfirm.explanation || 'Please confirm to continue this ForeTees action.'}
        </p>
        {pendingConfirm.screenshot_b64 && (
          <img
            alt="Current ForeTees page"
            src={`data:image/png;base64,${pendingConfirm.screenshot_b64}`}
            style={{
              width: '100%',
              maxHeight: 220,
              objectFit: 'contain',
              borderRadius: 8,
              border: `1px solid ${theme.colors.border || '#ddd'}`,
              marginBottom: 16,
              background: '#0f172a',
            }}
          />
        )}
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            type="button"
            onClick={() => onResolve?.(false)}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: 8,
              border: `1px solid ${theme.colors.border || '#ccc'}`,
              background: 'transparent',
              color: theme.colors.textPrimary,
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Deny
          </button>
          <button
            type="button"
            onClick={() => onResolve?.(true)}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: 8,
              border: 'none',
              background: '#10b981',
              color: '#fff',
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Allow
          </button>
        </div>
      </div>
    </>
  );
};

export default AgentConfirmDialog;
