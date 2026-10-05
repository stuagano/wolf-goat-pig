import React, { useCallback, useEffect, useState } from "react";
import PostRoundForm from "../components/rounds/PostRoundForm";
import { useAccessToken } from "../hooks/useAccessToken";
import { fetchMyRounds } from "../services/rounds";

const statusLabel = (status) => (status === "pending" ? "Previously pending" : "Posted");

const scoreClass = (score) => {
  const numericScore = Number(score);
  if (numericScore < 0) return "negative";
  if (numericScore > 0) return "positive";
  return "";
};

const RoundStatusBadge = ({ status }) => (
  <span className={`round-status-badge ${status === "pending" ? "pending" : "posted"}`}>
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const PostRoundPage = () => {
  const { getToken } = useAccessToken();

  const [myRounds, setMyRounds] = useState([]);
  const [myRoundsState, setMyRoundsState] = useState({ loading: true, error: "" });
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

  useEffect(() => { loadMyRounds(); }, [loadMyRounds]);

  return (
    <main className="post-round-page">
      <section className="hero-card">
        <p className="eyebrow">Member totals</p>
        <h1>Post a Round</h1>
        <p>
          Enter quarters won or lost for everyone in your foursome. One person submits
          the results, and they count immediately on the honor system.
        </p>
      </section>

      <section className="round-layout">
        <div className="round-card">
          <h2>Round Result</h2>
          <PostRoundForm onPosted={loadMyRounds} />
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
        .round-card h2 {
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
          grid-template-columns: minmax(0, 1fr);
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

        .round-status-badge.posted {
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

        }
      `}</style>
    </main>
  );
};

export default PostRoundPage;
