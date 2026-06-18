import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import LegacyNameSelector from "../components/auth/LegacyNameSelector";
import { useLegacyPlayers } from "../hooks/useLegacyPlayers";
import { usePlayerProfile } from "../hooks/usePlayerProfile";
import {
  attestRound,
  fetchMyRounds,
  fetchPendingAttestations,
  postMyRound,
} from "../services/rounds";

const todayLocalDate = () => {
  const now = new Date();
  const offsetMs = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offsetMs).toISOString().slice(0, 10);
};

const statusLabel = (status) => (status === "attested" ? "Attested" : "Pending");

const RoundStatusBadge = ({ status }) => (
  <span className={`round-status-badge ${status === "attested" ? "attested" : "pending"}`}>
    {statusLabel(status)}
  </span>
);

const RoundList = ({ rounds, loading, error, onRefresh }) => {
  if (loading) {
    return <p className="muted">Loading your rounds...</p>;
  }

  if (error) {
    return (
      <div className="round-alert error">
        <p>{error}</p>
        <button type="button" onClick={onRefresh}>Try again</button>
      </div>
    );
  }

  if (!rounds.length) {
    return <p className="muted">No posted rounds yet.</p>;
  }

  return (
    <div className="round-table-wrap">
      <table className="round-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Quarters</th>
            <th>Status</th>
            <th>Foursome</th>
            <th>Attested By</th>
          </tr>
        </thead>
        <tbody>
          {rounds.map((round) => (
            <tr key={round.id}>
              <td>{round.date}</td>
              <td className={Number(round.score) < 0 ? "negative" : "positive"}>
                {Number(round.score) > 0 ? "+" : ""}{round.score}
              </td>
              <td><RoundStatusBadge status={round.status} /></td>
              <td>{round.foursome?.join(", ") || "—"}</td>
              <td>{round.attested_by || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const AttestationQueue = ({ rounds, loading, error, attestingId, onAttest, onRefresh }) => {
  if (loading) {
    return <p className="muted">Loading attestation queue...</p>;
  }

  if (error) {
    return (
      <div className="round-alert error">
        <p>{error}</p>
        <button type="button" onClick={onRefresh}>Try again</button>
      </div>
    );
  }

  if (!rounds.length) {
    return <p className="muted">No rounds are awaiting your attestation.</p>;
  }

  return (
    <div className="attestation-list">
      {rounds.map((round) => (
        <article className="attestation-card" key={round.id}>
          <div>
            <h3>{round.member || "Member"}</h3>
            <p className="muted">{round.date} · WGP quarters {Number(round.score) > 0 ? "+" : ""}{round.score}</p>
            <p><strong>Foursome:</strong> {round.foursome?.join(", ") || "—"}</p>
          </div>
          <button
            type="button"
            onClick={() => onAttest(round.id)}
            disabled={attestingId === round.id}
          >
            {attestingId === round.id ? "Attesting..." : "Attest"}
          </button>
        </article>
      ))}
    </div>
  );
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
    <div className="foursome-picker">
      <div className="selected-foursome">
        {selectedNames.length ? selectedNames.map((name) => (
          <button type="button" key={name} onClick={() => togglePlayer(name)}>
            {name} ×
          </button>
        )) : <span className="muted">Select 1-3 other members who played with you.</span>}
      </div>
      <div className="player-grid" role="group" aria-label="Foursome members">
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

const PostRoundPage = () => {
  const { getAccessTokenSilently } = useAuth0();
  const {
    profile,
    loading: profileLoading,
    error: profileError,
    updateLegacyName,
    refetch: refetchProfile,
  } = usePlayerProfile();
  const { players, loading: rosterLoading, error: rosterError } = useLegacyPlayers();

  const [form, setForm] = useState({
    date: todayLocalDate(),
    score: "",
    location: "",
    group: "",
    duration: "",
    foursome: [],
  });
  const [submitState, setSubmitState] = useState({ loading: false, error: "", success: "" });
  const [showLinkFlow, setShowLinkFlow] = useState(false);
  const [myRounds, setMyRounds] = useState([]);
  const [myRoundsState, setMyRoundsState] = useState({ loading: true, error: "" });
  const [pendingRounds, setPendingRounds] = useState([]);
  const [pendingState, setPendingState] = useState({ loading: true, error: "" });
  const [attestingId, setAttestingId] = useState(null);
  const [attestMessage, setAttestMessage] = useState("");

  const legacyName = profile?.legacy_name || "";

  const getToken = useCallback(() => getAccessTokenSilently(), [getAccessTokenSilently]);

  const loadMyRounds = useCallback(async () => {
    setMyRoundsState({ loading: true, error: "" });
    try {
      const rounds = await fetchMyRounds(getToken);
      setMyRounds(rounds);
      setMyRoundsState({ loading: false, error: "" });
    } catch (error) {
      setMyRoundsState({ loading: false, error: error.message });
    }
  }, [getToken]);

  const loadPendingRounds = useCallback(async () => {
    setPendingState({ loading: true, error: "" });
    try {
      const rounds = await fetchPendingAttestations(getToken);
      setPendingRounds(rounds);
      setPendingState({ loading: false, error: "" });
    } catch (error) {
      setPendingState({ loading: false, error: error.message });
    }
  }, [getToken]);

  useEffect(() => {
    loadMyRounds();
    loadPendingRounds();
  }, [loadMyRounds, loadPendingRounds]);

  const updateForm = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitState({ loading: true, error: "", success: "" });
    setShowLinkFlow(false);

    if (form.foursome.length < 1 || form.foursome.length > 3) {
      setSubmitState({ loading: false, error: "Select 1-3 other foursome members.", success: "" });
      return;
    }

    if (!form.score.trim() || Number.isNaN(Number(form.score))) {
      setSubmitState({ loading: false, error: "Enter WGP quarters won/lost as a number.", success: "" });
      return;
    }

    try {
      await postMyRound(getToken, {
        date: form.date,
        score: Number(form.score),
        location: form.location.trim() || undefined,
        group: form.group.trim() || undefined,
        duration: form.duration.trim() || undefined,
        foursome: form.foursome,
      });
      setSubmitState({ loading: false, error: "", success: "Round posted for attestation." });
      setForm((current) => ({ ...current, score: "", location: "", group: "", duration: "", foursome: [] }));
      loadMyRounds();
    } catch (error) {
      const message = error.status === 409 ? "already posted for that date" : error.message;
      if (error.status === 400 && error.message === "Link your roster name first") {
        setShowLinkFlow(true);
      }
      setSubmitState({ loading: false, error: message, success: "" });
    }
  };

  const handleLegacySelect = async (name) => {
    await updateLegacyName(name);
    await refetchProfile();
    setShowLinkFlow(false);
    setSubmitState({ loading: false, error: "", success: "Roster name linked. You can post your round now." });
  };

  const handleAttest = async (roundId) => {
    setAttestingId(roundId);
    setAttestMessage("");
    try {
      const updatedRound = await attestRound(getToken, roundId);
      setPendingRounds((rounds) => rounds.filter((round) => round.id !== roundId));
      setMyRounds((rounds) => rounds.map((round) => (round.id === updatedRound.id ? updatedRound : round)));
      setAttestMessage("Round attested.");
    } catch (error) {
      setAttestMessage(error.message);
    } finally {
      setAttestingId(null);
    }
  };

  return (
    <main className="post-round-page">
      <section className="hero-card">
        <p className="eyebrow">Member totals</p>
        <h1>Post a Round</h1>
        <p>
          Enter the Wolf-Goat-Pig round result that goes into the sheet today:
          total quarters won or lost, plus the other members in your foursome.
        </p>
      </section>

      <section className="round-layout">
        <div className="round-card">
          <h2>Round Result</h2>
          {profileLoading && <p className="muted">Loading profile...</p>}
          {profileError && <div className="round-alert error">{profileError}</div>}
          {legacyName && <p className="linked-name">Posting as <strong>{legacyName}</strong></p>}
          {!legacyName && !profileLoading && (
            <div className="round-alert warning">Link your roster name before posting a round.</div>
          )}
          <form onSubmit={handleSubmit} className="round-form">
            <label>
              Date
              <input
                type="date"
                value={form.date}
                onChange={(event) => updateForm("date", event.target.value)}
                required
              />
            </label>

            <label>
              WGP quarters won/lost
              <input
                type="number"
                step="1"
                inputMode="numeric"
                value={form.score}
                onChange={(event) => updateForm("score", event.target.value)}
                placeholder="Example: -3 or 8"
                required
              />
            </label>

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

            <div>
              <label className="standalone-label">Foursome members</label>
              {rosterLoading ? (
                <p className="muted">Loading roster...</p>
              ) : rosterError ? (
                <div className="round-alert error">{rosterError}</div>
              ) : (
                <FoursomePicker
                  players={players}
                  currentName={legacyName}
                  selectedNames={form.foursome}
                  onChange={(foursome) => updateForm("foursome", foursome)}
                />
              )}
            </div>

            {submitState.error && <div className="round-alert error">{submitState.error}</div>}
            {submitState.success && <div className="round-alert success">{submitState.success}</div>}

            <button type="submit" disabled={submitState.loading || rosterLoading}>
              {submitState.loading ? "Posting..." : "Post Round"}
            </button>
          </form>

          {(showLinkFlow || (!legacyName && !profileLoading)) && (
            <div className="link-flow">
              <LegacyNameSelector
                currentName={legacyName}
                onSelect={handleLegacySelect}
                onSkip={() => setShowLinkFlow(false)}
              />
            </div>
          )}
        </div>

        <div className="round-card">
          <h2>Awaiting Your Attestation</h2>
          {attestMessage && <div className="round-alert success">{attestMessage}</div>}
          <AttestationQueue
            rounds={pendingRounds}
            loading={pendingState.loading}
            error={pendingState.error}
            attestingId={attestingId}
            onAttest={handleAttest}
            onRefresh={loadPendingRounds}
          />
        </div>
      </section>

      <section className="round-card my-rounds-card">
        <h2>My Rounds</h2>
        <RoundList
          rounds={myRounds}
          loading={myRoundsState.loading}
          error={myRoundsState.error}
          onRefresh={loadMyRounds}
        />
      </section>

      <style>{`
        .post-round-page {
          max-width: 1180px;
          margin: 0 auto;
          padding: 24px 16px 48px;
          color: #1f2937;
        }

        .hero-card,
        .round-card {
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 16px;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        }

        .hero-card {
          padding: 28px;
          margin-bottom: 24px;
          background: linear-gradient(135deg, #f0f7ed 0%, #ffffff 100%);
        }

        .hero-card h1,
        .round-card h2,
        .attestation-card h3 {
          margin: 0;
          color: #1f3b1b;
        }

        .hero-card p {
          max-width: 780px;
          margin: 10px 0 0;
          color: #4b5563;
          line-height: 1.5;
        }

        .eyebrow {
          text-transform: uppercase;
          letter-spacing: 0.08em;
          font-size: 12px;
          font-weight: 700;
          color: #2d5a27;
        }

        .round-layout {
          display: grid;
          grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
          gap: 24px;
          align-items: start;
        }

        .round-card {
          padding: 24px;
        }

        .my-rounds-card {
          margin-top: 24px;
        }

        .round-form {
          display: grid;
          gap: 16px;
          margin-top: 18px;
        }

        .round-form label,
        .standalone-label {
          display: grid;
          gap: 6px;
          font-weight: 700;
          color: #374151;
        }

        .round-form label span {
          font-weight: 500;
          color: #6b7280;
        }

        .round-form input {
          border: 1px solid #d1d5db;
          border-radius: 10px;
          padding: 11px 12px;
          font-size: 16px;
        }

        .round-form input:focus {
          outline: 2px solid #9acd7e;
          border-color: #2d5a27;
        }

        .round-form > button,
        .attestation-card button,
        .round-alert button {
          background: #2d5a27;
          color: #ffffff;
          border: none;
          border-radius: 10px;
          padding: 11px 16px;
          font-weight: 700;
          cursor: pointer;
        }

        .round-form > button:disabled,
        .attestation-card button:disabled,
        .player-grid button:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .linked-name {
          color: #4b5563;
        }

        .muted {
          color: #6b7280;
        }

        .round-alert {
          border-radius: 10px;
          padding: 12px 14px;
          margin: 12px 0;
        }

        .round-alert.error {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fecaca;
        }

        .round-alert.warning {
          background: #fef3c7;
          color: #92400e;
          border: 1px solid #fde68a;
        }

        .round-alert.success {
          background: #dcfce7;
          color: #166534;
          border: 1px solid #bbf7d0;
        }

        .selected-foursome {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          min-height: 42px;
          align-items: center;
          margin: 8px 0 12px;
        }

        .selected-foursome button,
        .player-grid button {
          border: 1px solid #d1d5db;
          border-radius: 999px;
          background: #f9fafb;
          color: #374151;
          padding: 8px 12px;
          cursor: pointer;
        }

        .selected-foursome button,
        .player-grid button.selected {
          background: #e7f5e4;
          border-color: #2d5a27;
          color: #1f3b1b;
          font-weight: 700;
        }

        .player-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 8px;
          max-height: 260px;
          overflow: auto;
          padding: 2px;
        }

        .attestation-list {
          display: grid;
          gap: 12px;
          margin-top: 16px;
        }

        .attestation-card {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          align-items: center;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 16px;
          background: #f9fafb;
        }

        .attestation-card p {
          margin: 6px 0 0;
        }

        .round-table-wrap {
          overflow-x: auto;
          margin-top: 16px;
        }

        .round-table {
          width: 100%;
          border-collapse: collapse;
        }

        .round-table th,
        .round-table td {
          padding: 12px;
          border-bottom: 1px solid #e5e7eb;
          text-align: left;
        }

        .round-table th {
          background: #f9fafb;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: #6b7280;
        }

        .positive {
          color: #166534;
          font-weight: 700;
        }

        .negative {
          color: #991b1b;
          font-weight: 700;
        }

        .round-status-badge {
          display: inline-flex;
          border-radius: 999px;
          padding: 4px 10px;
          font-size: 12px;
          font-weight: 700;
        }

        .round-status-badge.pending {
          background: #fef3c7;
          color: #92400e;
        }

        .round-status-badge.attested {
          background: #dcfce7;
          color: #166534;
        }

        .link-flow {
          margin-top: 20px;
          border-top: 1px solid #e5e7eb;
          padding-top: 20px;
        }

        @media (max-width: 900px) {
          .round-layout {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 640px) {
          .post-round-page {
            padding: 16px 10px 36px;
          }

          .hero-card,
          .round-card {
            padding: 18px;
          }

          .attestation-card {
            align-items: stretch;
            flex-direction: column;
          }
        }
      `}</style>
    </main>
  );
};

export default PostRoundPage;
