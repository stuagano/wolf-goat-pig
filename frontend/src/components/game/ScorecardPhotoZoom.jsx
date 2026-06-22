import React, { useState, useRef } from 'react';

/**
 * ScorecardPhotoZoom — full-screen zoom/pan viewer for the captured scorecard
 * photo, so the user can validate the scanned totals against what's on the card.
 * View-only. Pan by scrolling/dragging the container; zoom with the +/- buttons.
 * Opens scrolled to the right edge, where the TOT column lives.
 */
const MIN_SCALE = 1;
const MAX_SCALE = 6;
const STEP = 0.4;
const INITIAL_SCALE = 1.6;

const ScorecardPhotoZoom = ({ src, onClose }) => {
  const [scale, setScale] = useState(INITIAL_SCALE);
  const scrollRef = useRef(null);

  // On image load, jump to the right edge so the totals column is in view.
  const handleImgLoad = () => {
    const el = scrollRef.current;
    if (el) el.scrollLeft = el.scrollWidth;
  };

  const zoom = (delta) => setScale((s) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.round((s + delta) * 10) / 10)));

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex flex-col" role="dialog" aria-label="Scorecard photo">
      <div className="flex items-center justify-between p-3 text-white">
        <span className="text-xs text-white/70">Drag to pan · +/− to zoom</span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => zoom(-STEP)}
            aria-label="zoom out"
            className="w-10 h-10 rounded bg-white/20 hover:bg-white/30 text-2xl leading-none"
          >
            −
          </button>
          <button
            type="button"
            onClick={() => zoom(STEP)}
            aria-label="zoom in"
            className="w-10 h-10 rounded bg-white/20 hover:bg-white/30 text-2xl leading-none"
          >
            +
          </button>
          <button
            type="button"
            onClick={onClose}
            aria-label="close photo"
            className="w-10 h-10 rounded bg-white/20 hover:bg-white/30 text-2xl leading-none"
          >
            ✕
          </button>
        </div>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-auto">
        <img
          src={src}
          alt="scorecard"
          onLoad={handleImgLoad}
          style={{ width: `${scale * 100}%`, maxWidth: 'none' }}
          className="block select-none"
          draggable={false}
        />
      </div>
    </div>
  );
};

export default ScorecardPhotoZoom;
