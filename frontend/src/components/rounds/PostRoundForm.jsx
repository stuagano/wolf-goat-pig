import React, { useCallback, useMemo, useState } from "react";
import LegacyNameSelector from "../auth/LegacyNameSelector";
import { useLegacyPlayers } from "../../hooks/useLegacyPlayers";
import { usePlayerProfile } from "../../hooks/usePlayerProfile";
import { useAccessToken } from "../../hooks/useAccessToken";
import { postMyRound } from "../../services/rounds";

const todayLocalDate = () => {
  const now = new Date();
  const offsetMs = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 10);
};

const FoursomePicker = ({ players, currentName, selectedNames, onChange }) => {
  const availablePlayers = useMemo(
    () => players.filter((name) => name && name !== currentName),
    [players, currentName],
  );

  const togglePlayer = (name) => {
    if (selectedNames.includes(name)) {
      onChange(selectedNames.filter((selectedName) => selectedName !== name));
      return;
    }

    if (selectedNames.length < 3) {
      onChange([...selectedNames, name]);
    }
  };

  return (
    <div className="pr-foursome-picker">
      <div className="pr-selected-foursome">
        {selectedNames.length ? (
          selectedNames.map((name) => (
            <button type="button" key={name} onClick={() => togglePlayer(name)}>
              {name} ×
            </button>
          ))
        ) : (
          <span className="pr-muted">Select 1-3 other members who played with you.</span>
        )}
      </div>
      <div className="pr-player-grid" role="group" aria-label="Foursome members">
        {availablePlayers.map((name) => {
          const selected = selectedNames.includes(name);
          return (
            <button
              type="button"
              key={name}
              className={selected ? "selected" : ""}
              onClick={() => togglePlayer(name)}
              disabled={!selected && selectedNames.length >= 3}
            >
              {name}
            </button>
          );
        })}
      </div>
    </div>
  );
};

/**
 * Self-contained "post a Wolf-Goat-Pig round result" form.
 *
 * Handles legacy-name linking, foursome selection, and — critically — recovers
 * from the "Missing Refresh Token" auth error: submission uses a resilient token
 * getter, and if auth still can't be recovered the user gets an explicit
 * "Try again" / "Sign in again" choice instead of a dead-end error.
 *
 * @param {object} props
 * @param {() => void} [props.onPosted] - called after a round is posted (refresh lists)
 * @param {boolean} [props.compact] - tighter layout for embedding (e.g. home page)
 */
const PostRoundForm = ({ onPosted, compact = false }) => {
  const { getToken, reauthenticate, isRecoverableAuthError } = useAccessToken();
  const {
    profile,
    loading: profileLoading,
    error: profileError,
    updateLegacyName,
  } = usePlayerProfile();
  const { players, loading: rosterLoading, error: rosterError } = useLegacyPlayers();

  const [form, setForm] = useState({
    date: todayLocalDate(),
    scores: {},
    location: "",
    group: "",
    duration: "",
    foursome: [],
  });
  const [submitState, setSubmitState] = useState({
    loading: false,
    error: "",
    success: "",
    canRetry: false,
    needsReauth: false,
  });
  const [showLinkFlow, setShowLinkFlow] = useState(false);

  const legacyName = profile?.legacy_name || "";

  const updateForm = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submitRound = useCallback(async () => {
    setSubmitState({ loading: true, error: "", success: "", canRetry: false, needsReauth: false });
    setShowLinkFlow(false);

    if (form.foursome.length < 1 || form.foursome.length > 3) {
      setSubmitState({
        loading: false,
        error: "Select 1-3 other foursome members.",
        success: "",
        canRetry: false,
        needsReauth: false,
      });
      return;
    }

    const members = [legacyName, ...form.foursome];
    const missingOrInvalidScore = members.some(name => (
      form.scores[name] == null || String(form.scores[name]).trim() === "" ||
      !Number.isInteger(Number(form.scores[name]))
    ));
    if (!legacyName || missingOrInvalidScore) {
      setSubmitState({
        loading: false,
        error: "Enter whole quarters won/lost for every player, including zero.",
        success: "",
        canRetry: false,
        needsReauth: false,
      });
      return;
    }

    try {
      const posted = await postMyRound(getToken, {
        date: form.date,
        results: members.map(member => ({ member, score: Number(form.scores[member]) })),
        location: form.location.trim() || undefined,
        group: form.group.trim() || undefined,
        duration: form.duration.trim() || undefined,
      });
      setSubmitState({
        loading: false,
        error: "",
        success: `Results posted for all ${posted.rounds.length} players. They count immediately on the honor system.`,
        canRetry: false,
        needsReauth: false,
      });
      setForm((current) => ({
        ...current,
        scores: {},
        location: "",
        group: "",
        duration: "",
        foursome: [],
      }));
      if (onPosted) onPosted();
    } catch (error) {
      if (isRecoverableAuthError(error)) {
        // Silent refresh + fallback both failed — the session needs a real login.
        setSubmitState({
          loading: false,
          error: "Your sign-in expired. Try again, or sign in again to post your score.",
          success: "",
          canRetry: true,
          needsReauth: true,
        });
        return;
      }
      const message = error.message;
      setSubmitState({
        loading: false,
        error: message,
        success: "",
        canRetry: error.status !== 400 && error.status !== 409,
        needsReauth: false,
      });
      if (error.status === 400 && /link your roster/i.test(error.message)) {
        setShowLinkFlow(true);
      }
    }
  }, [form, legacyName, getToken, isRecoverableAuthError, onPosted]);

  const handleSubmit = (event) => {
    event.preventDefault();
    submitRound();
  };

  const handleLegacySelect = async (name) => {
    await updateLegacyName(name);
    setShowLinkFlow(false);
    setSubmitState({
      loading: false,
      error: "",
      success: "Roster name linked. You can post your round now.",
      canRetry: false,
      needsReauth: false,
    });
  };

  return (
    <div className={`pr-form-root ${compact ? "compact" : ""}`}>
      {profileLoading && <p className="pr-muted">Loading profile...</p>}
      {profileError && <div className="pr-alert error">{profileError}</div>}
      {legacyName && (
        <p className="pr-linked-name">
          Posting as <strong>{legacyName}</strong>
        </p>
      )}
      {!legacyName && !profileLoading && (
        <div className="pr-alert warning">Link your roster name before posting a round.</div>
      )}

      <form onSubmit={handleSubmit} className="pr-form">
        <div className="pr-field-row">
          <label>
            Date
            <input
              type="date"
              value={form.date}
              onChange={(event) => updateForm("date", event.target.value)}
              required
            />
          </label>
        </div>

        {!compact && (
          <div className="pr-field-row">
            <label>
              Location <span>(optional)</span>
              <input
                type="text"
                value={form.location}
                onChange={(event) => updateForm("location", event.target.value)}
                placeholder="Wing Point"
              />
            </label>

            <label>
              Group <span>(optional)</span>
              <input
                type="text"
                value={form.group}
                onChange={(event) => updateForm("group", event.target.value)}
                placeholder="Morning game"
              />
            </label>

            <label>
              Duration <span>(optional)</span>
              <input
                type="text"
                value={form.duration}
                onChange={(event) => updateForm("duration", event.target.value)}
                placeholder="18 holes"
              />
            </label>
          </div>
        )}

        <div>
          <label className="pr-standalone-label">Foursome members</label>
          {rosterLoading ? (
            <p className="pr-muted">Loading roster...</p>
          ) : rosterError ? (
            <div className="pr-alert error">{rosterError}</div>
          ) : (
            <FoursomePicker
              players={players}
              currentName={legacyName}
              selectedNames={form.foursome}
              onChange={(foursome) => updateForm("foursome", foursome)}
            />
          )}
        </div>

        <fieldset className="pr-field-row" disabled={submitState.loading}>
          <legend>Everyone's quarters won/lost</legend>
          {[legacyName, ...form.foursome].filter(Boolean).map(name => (
            <label key={name}>
              {name} — quarters won/lost
              <input type="number" step="1" min="-2147483648" max="2147483647" inputMode="numeric"
                value={form.scores[name] ?? ""} required placeholder="Example: -3, 0, or 8"
                onChange={event => setForm(current => ({ ...current, scores: { ...current.scores, [name]: event.target.value } }))}
              />
            </label>
          ))}
        </fieldset>
        <p className="pr-muted">One person posts for the group. Results count immediately on the honor system.</p>

        {submitState.error && (
          <div className="pr-alert error">
            <p>{submitState.error}</p>
            {(submitState.canRetry || submitState.needsReauth) && (
              <div className="pr-alert-actions">
                {submitState.canRetry && (
                  <button type="button" onClick={submitRound} disabled={submitState.loading}>
                    Try again
                  </button>
                )}
                {submitState.needsReauth && (
                  <button type="button" className="secondary" onClick={reauthenticate}>
                    Sign in again
                  </button>
                )}
              </div>
            )}
          </div>
        )}
        {submitState.success && <div className="pr-alert success">{submitState.success}</div>}

        <button type="submit" className="pr-submit" disabled={submitState.loading || rosterLoading || !legacyName}>
          {submitState.loading ? "Posting..." : "Post foursome results"}
        </button>
      </form>

      {(showLinkFlow || (!legacyName && !profileLoading)) && (
        <div className="pr-link-flow">
          <LegacyNameSelector
            currentName={legacyName}
            onSelect={handleLegacySelect}
            onSkip={() => setShowLinkFlow(false)}
          />
        </div>
      )}

      <style>{`
        .pr-form-root {
          color: #1f2937;
        }

        .pr-form {
          display: grid;
          gap: 16px;
          margin-top: 12px;
        }

        .pr-field-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
          gap: 16px;
        }

        .pr-form label,
        .pr-standalone-label {
          display: grid;
          gap: 6px;
          font-weight: 700;
          color: #374151;
        }

        .pr-form label span {
          font-weight: 500;
          color: #6b7280;
        }

        .pr-form input {
          border: 1px solid #d1d5db;
          border-radius: 10px;
          padding: 11px 12px;
          font-size: 16px;
        }

        .pr-form input:focus {
          outline: 2px solid #9acd7e;
          border-color: #2d5a27;
        }

        .pr-submit,
        .pr-alert button {
          background: #2d5a27;
          color: #ffffff;
          border: none;
          border-radius: 10px;
          padding: 11px 16px;
          font-weight: 700;
          cursor: pointer;
        }

        .pr-alert button.secondary {
          background: #ffffff;
          color: #2d5a27;
          border: 1px solid #2d5a27;
        }

        .pr-submit:disabled,
        .pr-player-grid button:disabled,
        .pr-alert button:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .pr-linked-name {
          color: #4b5563;
        }

        .pr-muted {
          color: #6b7280;
        }

        .pr-alert {
          border-radius: 10px;
          padding: 12px 14px;
          margin: 4px 0;
        }

        .pr-alert p {
          margin: 0;
        }

        .pr-alert-actions {
          display: flex;
          gap: 10px;
          margin-top: 10px;
          flex-wrap: wrap;
        }

        .pr-alert.error {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fecaca;
        }

        .pr-alert.warning {
          background: #fef3c7;
          color: #92400e;
          border: 1px solid #fde68a;
        }

        .pr-alert.success {
          background: #dcfce7;
          color: #166534;
          border: 1px solid #bbf7d0;
        }

        .pr-selected-foursome {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          min-height: 42px;
          align-items: center;
          margin: 8px 0 12px;
        }

        .pr-selected-foursome button,
        .pr-player-grid button {
          border: 1px solid #d1d5db;
          border-radius: 999px;
          background: #f9fafb;
          color: #374151;
          padding: 8px 12px;
          cursor: pointer;
        }

        .pr-selected-foursome button,
        .pr-player-grid button.selected {
          background: #e7f5e4;
          border-color: #2d5a27;
          color: #1f3b1b;
          font-weight: 700;
        }

        .pr-player-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 8px;
          max-height: 260px;
          overflow: auto;
          padding: 2px;
        }

        .pr-form-root.compact .pr-player-grid {
          max-height: 180px;
        }

        .pr-link-flow {
          margin-top: 20px;
          border-top: 1px solid #e5e7eb;
          padding-top: 20px;
        }
      `}</style>
    </div>
  );
};

export default PostRoundForm;
