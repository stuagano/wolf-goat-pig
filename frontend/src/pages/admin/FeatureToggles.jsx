import React, { useState, useEffect } from 'react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { Card } from '../../components/ui';
import { apiConfig } from '../../config/api.config';

const API_URL = apiConfig.baseUrl;

const FLAG_LABELS = {
  foretees: { label: 'ForeTees booking', description: 'Tee time booking tab on the sign-up page' },
  scorecard_scan: { label: 'Scorecard scanning', description: 'Post-round photo-to-score flow' },
  livsow: { label: 'LivSow', description: 'LivSow leaderboard and team pages' },
  commissioner_chat: { label: 'Commissioner chat', description: 'League chat (GroupMe bridge)' },
};

export default function FeatureToggles() {
  const authenticatedFetch = useAuthenticatedFetch();
  const [flags, setFlags] = useState(null);
  const [saving, setSaving] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/config/features`)
      .then((r) => r.json())
      .then((d) => setFlags(d.features))
      .catch(() => setError('Failed to load feature flags'));
  }, []);

  const toggle = async (key) => {
    const updated = { [key]: !flags[key] };
    setSaving(key);
    setError(null);
    try {
      const res = await authenticatedFetch(`${API_URL}/config/features`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updated),
      });
      const data = await res.json();
      if (res.ok) {
        setFlags(data.features);
      } else {
        setError(data.detail || 'Save failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(null);
    }
  };

  if (!flags) return <div className="p-6 text-gray-500">{error || 'Loading…'}</div>;

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-2">Feature Toggles</h2>
      <p className="text-gray-500 text-sm mb-6">
        Turn features on or off without a deploy. Changes take effect on next page load.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      <div className="space-y-3 max-w-lg">
        {Object.entries(FLAG_LABELS).map(([key, { label, description }]) => (
          <div
            key={key}
            className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
          >
            <div>
              <div className="font-medium text-gray-900">{label}</div>
              <div className="text-sm text-gray-500">{description}</div>
            </div>
            <button
              onClick={() => toggle(key)}
              disabled={saving === key}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none disabled:opacity-50 ${
                flags[key] ? 'bg-green-600' : 'bg-gray-300'
              }`}
              aria-checked={flags[key]}
              role="switch"
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition duration-200 ${
                  flags[key] ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        ))}
      </div>
    </Card>
  );
}
