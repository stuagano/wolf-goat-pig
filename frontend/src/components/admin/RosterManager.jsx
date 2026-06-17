import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { Card } from "../ui";
import {
  isAdminEmail,
  getStoredUserEmail,
  adminHeaders,
} from "../../utils/adminAuth";
import { apiConfig } from "../../config/api.config";

const API_URL = apiConfig.baseUrl;

/**
 * Organizer-facing roster management.
 *
 * Wraps the admin legacy-roster endpoints (all gated by X-Admin-Email):
 *   GET  /legacy-players/pending            — capture queue
 *   POST /legacy-players/pending/{id}/promote
 *   POST /legacy-players/pending/{id}/dismiss
 *   POST /legacy-players  {name}            — add to canonical roster
 *
 * Promote a captured golfer once they exist on Jeff's legacy dropdown;
 * dismiss a misspelling. Add a name directly when you already know it is
 * on the dropdown.
 */
const RosterManager = () => {
  const navigate = useNavigate();
  const { user, isLoading: authLoading } = useAuth0();

  const [isAdmin, setIsAdmin] = useState(false);
  const [checkingAdmin, setCheckingAdmin] = useState(true);

  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");

  const [newName, setNewName] = useState("");
  const [adding, setAdding] = useState(false);
  const [actingId, setActingId] = useState(null);

  // Auth0 identity is authoritative; stored email is a fallback on reload.
  // No hardcoded default — unknown users are never admins.
  useEffect(() => {
    if (authLoading) return;
    const email = user?.email || getStoredUserEmail();
    setIsAdmin(isAdminEmail(email));
    setCheckingAdmin(false);
  }, [authLoading, user]);

  const fetchPending = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/legacy-players/pending?status=pending`, {
        headers: adminHeaders(),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setPending(data.players || []);
    } catch (err) {
      setError(`Could not load pending players: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAdmin) {
      fetchPending();
    }
  }, [isAdmin, fetchPending]);

  const addName = async (e) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;

    setAdding(true);
    setFeedback("");
    setError("");
    try {
      const response = await fetch(`${API_URL}/legacy-players`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...adminHeaders(),
        },
        body: JSON.stringify({ name }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      if (data.added) {
        setFeedback(`✓ Added "${data.canonical_name || name}" to the roster`);
      } else {
        setFeedback(data.message || `"${name}" is already in the roster`);
      }
      setNewName("");
    } catch (err) {
      setError(`Could not add player: ${err.message}`);
    } finally {
      setAdding(false);
    }
  };

  const promote = async (player) => {
    setActingId(player.id);
    setFeedback("");
    setError("");
    try {
      const response = await fetch(
        `${API_URL}/legacy-players/pending/${player.id}/promote`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json", ...adminHeaders() },
        },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      setFeedback(`✓ Promoted "${player.name}" to the canonical roster`);
      await fetchPending();
    } catch (err) {
      setError(`Could not promote "${player.name}": ${err.message}`);
    } finally {
      setActingId(null);
    }
  };

  const dismiss = async (player) => {
    setActingId(player.id);
    setFeedback("");
    setError("");
    try {
      const response = await fetch(
        `${API_URL}/legacy-players/pending/${player.id}/dismiss`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json", ...adminHeaders() },
        },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      setFeedback(`✓ Dismissed "${player.name}"`);
      await fetchPending();
    } catch (err) {
      setError(`Could not dismiss "${player.name}": ${err.message}`);
    } finally {
      setActingId(null);
    }
  };

  if (checkingAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div
          className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"
          data-testid="roster-loading"
        ></div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <Card className="p-8 text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-4">
              Access Denied
            </h2>
            <p className="text-gray-600 mb-6">
              You don't have permission to access this page.
            </p>
            <button
              onClick={() => navigate("/")}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go to Home
            </button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            👥 Roster Management
          </h1>
          <p className="text-gray-600">
            Promote captured sign-ups onto the canonical legacy roster, or add a
            name directly once it exists on the tee-sheet dropdown.
          </p>
        </div>

        {feedback && (
          <div
            className="mb-6 p-4 rounded-lg bg-green-100 text-green-800"
            data-testid="roster-feedback"
          >
            {feedback}
          </div>
        )}
        {error && (
          <div
            className="mb-6 p-4 rounded-lg bg-red-100 text-red-800"
            data-testid="roster-error"
          >
            {error}
          </div>
        )}

        {/* Add a name directly to the canonical roster */}
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Add to Canonical Roster</h2>
          <p className="text-sm text-gray-600 mb-4">
            Use this once the player is known to exist on Jeff's legacy dropdown.
          </p>
          <form onSubmit={addName} className="flex space-x-4">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Player full name (e.g. Jane Smith)"
              aria-label="Player full name"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="submit"
              disabled={!newName.trim() || adding}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {adding ? "Adding..." : "Add Player"}
            </button>
          </form>
        </Card>

        {/* Pending capture queue */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">
              Pending Sign-ups{" "}
              {pending.length > 0 && (
                <span className="text-gray-500 font-normal">
                  ({pending.length})
                </span>
              )}
            </h2>
            <button
              onClick={fetchPending}
              disabled={loading}
              className="text-sm px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
            >
              {loading ? "Refreshing..." : "Refresh"}
            </button>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Golfers who signed up in the app but have no canonical match yet.
            Promote once they're on the dropdown, or dismiss a misspelling.
          </p>

          {loading ? (
            <div className="py-8 text-center text-gray-500" data-testid="pending-loading">
              Loading pending players...
            </div>
          ) : pending.length === 0 ? (
            <div
              className="py-8 text-center text-gray-500"
              data-testid="pending-empty"
            >
              No pending sign-ups. The capture queue is clear. 🎉
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {pending.map((player) => (
                <li
                  key={player.id}
                  data-testid={`pending-row-${player.id}`}
                  className="py-4 flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-gray-900">{player.name}</p>
                    {player.email && (
                      <p className="text-sm text-gray-500">{player.email}</p>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => promote(player)}
                      disabled={actingId === player.id}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {actingId === player.id ? "..." : "Promote"}
                    </button>
                    <button
                      onClick={() => dismiss(player)}
                      disabled={actingId === player.id}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                    >
                      {actingId === player.id ? "..." : "Dismiss"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
};

export default RosterManager;
