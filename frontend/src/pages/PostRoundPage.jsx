import React, { useCallback, useEffect, useState } from "react";
import PostRoundForm from "../components/rounds/PostRoundForm";
import { useAccessToken } from "../hooks/useAccessToken";
import {
  attestRound,
  fetchMyRounds,
  fetchPendingAttestations,
} from "../services/rounds";

const statusLabel = (status) => (status === "attested" ? "Attested" : "Pending");

const scoreClass = (score) => {
  const numericScore = Number(score);
  if (numericScore < 0) return "negative";
  if (numericScore > 0) return "positive";
  return "";
};

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
              <td className={scoreClass(round.score)}>
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

const PostRoundPage = () => {
  const { getToken } = useAccessToken();

  const [myRounds, setMyRounds] = useState([]);
  const [myRoundsState, setMyRoundsState] = useState({ loading: true, error: "" });
  const [pendingRounds, setPendingRounds] = useState([]);
  const [pendingState, setPendingState] = useState({ loading: true, error: "" });
  const [attestingId, setAttestingId] = useState(null);
  const [attestState, setAttestState] = useState({ error: "", success: "" });

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

  const handleAttest = async (roundId) => {
    setAttestingId(roundId);
    setAttestState({ error: "", success: "" });
    try {
      const updatedRound = await attestRound(getToken, roundId);
      setPendingRounds((rounds) => rounds.filter((round) => round.id !== roundId));
      setMyRounds((rounds) => rounds.map((round) => (round.id === updatedRound.id ? updatedRound : round)));
      setAttestState({ error: "", success: "Round attested." });
    } catch (error) {
      setAttestState({ error: error.message, success: "" });
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
          <PostRoundForm onPosted={loadMyRounds} />
        </div>

        <div className="round-card">
          <h2>Awaiting Your Attestation</h2>
          {attestState.error && <div className="round-alert error">{attestState.error}</div>}
          {attestState.success && <div className="round-alert success">{attestState.success}</div>}
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

        .muted {
          color: #6b7280;
        }

        .round-alert {
          border-radius: 10px;
          padding: 12px 14px;
          margin: 12px 0;
        }

        .round-alert button {
          background: #2d5a27;
          color: #ffffff;
          border: none;
          border-radius: 10px;
          padding: 11px 16px;
          font-weight: 700;
          cursor: pointer;
        }

        .round-alert.error {
          background: #fee2e2;
          color: #991b1b;
          border: 1px solid #fecaca;
        }

        .round-alert.success {
          background: #dcfce7;
          color: #166534;
          border: 1px solid #bbf7d0;
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

        .attestation-card button {
          background: #2d5a27;
          color: #ffffff;
          border: none;
          border-radius: 10px;
          padding: 11px 16px;
          font-weight: 700;
          cursor: pointer;
        }

        .attestation-card button:disabled {
          opacity: 0.55;
          cursor: not-allowed;
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
