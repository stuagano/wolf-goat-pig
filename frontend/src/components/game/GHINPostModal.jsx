import React, { useState, useEffect, useCallback } from 'react';
import { apiConfig } from '../../config/api.config';

const API_URL = apiConfig.baseUrl;

/**
 * GHINPostModal — optional step after saving WGP quarters.
 *
 * Props:
 *   players    — [{id, name}] from the game (used to pick "which player is you")
 *   playedAt   — ISO date string YYYY-MM-DD (defaults to today)
 *   onPosted   — called after successful GHIN post
 *   onSkip     — called if user skips
 */
const GHINPostModal = ({ players, playedAt, onPosted, onSkip }) => {
  const [ghinId, setGhinId] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [playerGhinMap, setPlayerGhinMap] = useState({});

  const [courseQuery, setCourseQuery] = useState('');
  const [courseResults, setCourseResults] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedTee, setSelectedTee] = useState(null);

  const [grossScore, setGrossScore] = useState('');
  const [date, setDate] = useState(playedAt || new Date().toISOString().slice(0, 10));

  const [courseLoading, setCourseLoading] = useState(false);
  const [posting, setPosting] = useState(false);
  const [error, setError] = useState(null);
  const [posted, setPosted] = useState(false);

  // Load GHIN IDs for all players in the game
  useEffect(() => {
    const load = async () => {
      try {
        const resp = await fetch(`${API_URL}/players`);
        if (!resp.ok) return;
        const all = await resp.json();
        const map = {};
        for (const p of all) {
          if (p.ghin_id) map[p.name] = p.ghin_id;
        }
        setPlayerGhinMap(map);

        // Auto-select if exactly one player in the game has a GHIN ID
        const withGhin = players.filter(p => map[p.name]);
        if (withGhin.length === 1) {
          setSelectedPlayer(withGhin[0].name);
          setGhinId(map[withGhin[0].name]);
        }
      } catch (_) {}
    };
    load();
  }, [players]);

  const handlePlayerSelect = (name) => {
    setSelectedPlayer(name);
    setGhinId(playerGhinMap[name] || '');
  };

  // Debounced course search
  useEffect(() => {
    if (courseQuery.length < 3) { setCourseResults([]); return; }
    const t = setTimeout(async () => {
      setCourseLoading(true);
      try {
        const resp = await fetch(`${API_URL}/ghin/courses?q=${encodeURIComponent(courseQuery)}`);
        if (resp.ok) {
          const data = await resp.json();
          setCourseResults(data.courses || []);
        }
      } catch (_) {}
      setCourseLoading(false);
    }, 400);
    return () => clearTimeout(t);
  }, [courseQuery]);

  const selectCourse = useCallback((course) => {
    setSelectedCourse(course);
    setCourseResults([]);
    setCourseQuery(course.FullName || course.CourseName || '');
    setSelectedTee(null);
  }, []);

  const handleSubmit = async () => {
    if (!ghinId || !selectedCourse || !selectedTee || !grossScore) return;
    setPosting(true);
    setError(null);
    try {
      const resp = await fetch(`${API_URL}/ghin/post-score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ghin_id: ghinId,
          course_id: selectedCourse.CourseID,
          tee_set_rating_id: selectedTee.TeeSetRatingId,
          gross_score: parseInt(grossScore, 10),
          played_at: date,
          number_of_holes: 18,
        }),
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.detail || `GHIN error ${resp.status}`);
      }
      setPosted(true);
      setTimeout(() => onPosted(), 1500);
    } catch (err) {
      setError(err.message);
    }
    setPosting(false);
  };

  if (posted) {
    return (
      <div className="flex flex-col items-center gap-4 p-8 text-center">
        <div className="text-5xl">✅</div>
        <p className="text-lg font-semibold text-green-700">Score posted to GHIN!</p>
      </div>
    );
  }

  const tees = selectedCourse?.Facilities || [];
  const canSubmit = ghinId && selectedCourse && selectedTee && grossScore && !posting;

  return (
    <div className="flex flex-col gap-5 p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Post Score to GHIN</h2>
        <button onClick={onSkip} className="text-sm text-gray-400 hover:text-gray-600">Skip</button>
      </div>

      {/* Player selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Your player</label>
        <div className="flex flex-wrap gap-2">
          {players.map(p => {
            const hasGhin = !!playerGhinMap[p.name];
            return (
              <button
                key={p.name}
                onClick={() => hasGhin && handlePlayerSelect(p.name)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                  selectedPlayer === p.name
                    ? 'bg-blue-600 text-white border-blue-600'
                    : hasGhin
                    ? 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
                    : 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                }`}
                title={!hasGhin ? 'No GHIN ID on file — add one on the Players page' : undefined}
              >
                {p.name}
                {!hasGhin && <span className="ml-1 text-xs opacity-60">no GHIN</span>}
              </button>
            );
          })}
        </div>
        {selectedPlayer && ghinId && (
          <p className="text-xs text-gray-400 mt-1">GHIN #{ghinId}</p>
        )}
      </div>

      {/* Gross score */}
      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Gross score</label>
          <input
            type="number"
            value={grossScore}
            onChange={e => setGrossScore(e.target.value)}
            placeholder="e.g. 87"
            min={54}
            max={180}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:outline-none"
          />
        </div>
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Date played</label>
          <input
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:outline-none"
          />
        </div>
      </div>

      {/* Course search */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Course</label>
        <div className="relative">
          <input
            type="text"
            value={courseQuery}
            onChange={e => { setCourseQuery(e.target.value); setSelectedCourse(null); setSelectedTee(null); }}
            placeholder="Search by course name..."
            className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-400 focus:outline-none"
          />
          {courseLoading && (
            <span className="absolute right-3 top-2.5 text-gray-400 text-xs">Searching...</span>
          )}
        </div>
        {courseResults.length > 0 && (
          <ul className="mt-1 border rounded-lg shadow-sm bg-white max-h-48 overflow-y-auto text-sm">
            {courseResults.map(c => (
              <li
                key={c.CourseID}
                onClick={() => selectCourse(c)}
                className="px-3 py-2 hover:bg-blue-50 cursor-pointer border-b last:border-0"
              >
                <span className="font-medium">{c.FullName || c.CourseName}</span>
                {c.City && <span className="text-gray-400 ml-2">{c.City}, {c.StateCode}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Tee selector */}
      {selectedCourse && tees.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tees</label>
          <div className="flex flex-wrap gap-2">
            {tees
              .filter(t => !t.Gender || t.Gender === 'M')
              .map(t => (
                <button
                  key={t.TeeSetRatingId}
                  onClick={() => setSelectedTee(t)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                    selectedTee?.TeeSetRatingId === t.TeeSetRatingId
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
                  }`}
                >
                  {t.TeeSetRatingName}
                  {t.CourseRating && (
                    <span className="ml-1 text-xs opacity-75">
                      {t.CourseRating}/{t.SlopeRating}
                    </span>
                  )}
                </button>
              ))}
          </div>
        </div>
      )}
      {selectedCourse && tees.length === 0 && (
        <p className="text-sm text-yellow-600">No tee data for this course — tee sets may need to be loaded separately.</p>
      )}

      {error && (
        <div className="bg-red-50 border border-red-300 rounded-lg p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="w-full py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {posting ? 'Posting...' : 'Post to GHIN'}
      </button>
    </div>
  );
};

export default GHINPostModal;
