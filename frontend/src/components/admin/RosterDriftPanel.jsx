import React, { useState } from "react";
import { Card } from "../ui";
import { useAuthenticatedFetch } from "../../hooks/useAuthenticatedFetch";
import { apiConfig } from "../../config/api.config";

const API_URL = apiConfig.baseUrl;
const linkButton = "text-blue-700 underline disabled:opacity-50";

/**
 * Compares the app roster with Jeff's live legacy dropdown (read-only):
 *   GET    /legacy-players/drift
 *   POST   /legacy-players {name}   — add a name that's on the dropdown
 *   DELETE /legacy-players/{name}   — remove a junk entry no profile uses
 */
const RosterDriftPanel = () => {
  const request = useAuthenticatedFetch();
  const [drift, setDrift] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");

  const call = async (path, options) => {
    const response = await request(`${API_URL}${path}`, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : `HTTP ${response.status}`);
    return data;
  };

  const compare = async () => {
    setBusy(true); setError(""); setFeedback("");
    try { setDrift(await call("/legacy-players/drift")); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const act = async (action, message) => {
    setBusy(true); setError(""); setFeedback("");
    try { await action(); setDrift(await call("/legacy-players/drift")); setFeedback(message); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const add = name => act(
    () => call("/legacy-players", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) }),
    `Added '${name}' to the roster.`,
  );
  const remove = name => act(
    () => call(`/legacy-players/${encodeURIComponent(name)}`, { method: "DELETE" }),
    `Removed '${name}' from the roster.`,
  );

  return (
    <Card className="p-6 mb-6">
      <h2 className="text-xl font-semibold mb-2">Compare with old site</h2>
      <p className="text-sm text-gray-600 mb-4">
        Checks the app roster against the player dropdown on Jeff's tee sheet. Sign-ups only go through for names on that dropdown.
      </p>
      <button type="button" className="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50" onClick={compare} disabled={busy}>
        {busy ? "Checking…" : "Compare now"}
      </button>
      {error && <div role="alert" className="mt-4 p-3 rounded-lg bg-red-50 text-red-800">{error}</div>}
      {feedback && <div role="status" className="mt-4 p-3 rounded-lg bg-green-50 text-green-800">{feedback}</div>}
      {drift && (
        <div className="mt-4 space-y-4 text-sm">
          <p>Old site: {drift.dropdown_count} names · App roster: {drift.roster_count} names</p>
          <section>
            <h3 className="font-semibold">On the old site, missing from the app ({drift.missing.length})</h3>
            {drift.missing.length === 0 ? <p className="text-gray-500">None.</p> : (
              <ul>{drift.missing.map(name => (
                <li key={name} className="flex justify-between py-1">
                  <span>{name}</span>
                  <button type="button" className={linkButton} disabled={busy} onClick={() => add(name)} aria-label={`Add ${name}`}>Add</button>
                </li>
              ))}</ul>
            )}
          </section>
          <section>
            <h3 className="font-semibold">Junk entries — emails or single words ({drift.junk.length})</h3>
            {drift.junk.length === 0 ? <p className="text-gray-500">None.</p> : (
              <ul>{drift.junk.map(({ name, used_by: usedBy }) => (
                <li key={name} className="flex justify-between py-1">
                  <span>{name}</span>
                  {usedBy.length === 0
                    ? <button type="button" className="text-red-700 underline disabled:opacity-50" disabled={busy} onClick={() => remove(name)} aria-label={`Remove ${name}`}>Remove</button>
                    : <span className="text-gray-500">Used by profile {usedBy.map(id => `#${id}`).join(", ")} — relink first</span>}
                </li>
              ))}</ul>
            )}
          </section>
          <section>
            <h3 className="font-semibold">In the app but not on the old site ({drift.not_on_dropdown.length})</h3>
            <p className="text-gray-500">Usually past players from round history. Kept so their history still matches.</p>
            {drift.not_on_dropdown.length > 0 && <p className="mt-1">{drift.not_on_dropdown.join(", ")}</p>}
          </section>
        </div>
      )}
    </Card>
  );
};

export default RosterDriftPanel;
