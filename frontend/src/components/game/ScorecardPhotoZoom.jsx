import React, { useState, useRef } from 'react';

const MIN_SCALE = 1;
const MAX_SCALE = 6;
const STEP = 0.4;

/** Shared photo controls: overlay for scanning, embedded for completed-round review. */
const ScorecardPhotoZoom = ({ src, onClose, embedded = false, onLoad, onError }) => {
  const [scale, setScale] = useState(embedded ? 1 : 1.6);
  const scrollRef = useRef(null);
  const drag = useRef(null);

  const zoom = (delta) => setScale((s) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.round((s + delta) * 10) / 10)));
  const reset = () => {
    setScale(1);
    if (scrollRef.current) {
      scrollRef.current.scrollLeft = 0;
      scrollRef.current.scrollTop = 0;
    }
  };

  return (
    <div
      className={embedded ? 'flex flex-col h-full min-h-0 bg-slate-900 rounded-lg overflow-hidden' : 'fixed inset-0 z-50 bg-black/90 flex flex-col'}
      role={embedded ? undefined : 'dialog'}
      aria-label="Scorecard photo"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 p-2 text-white">
        <span className="text-xs text-white/70">Drag or scroll to pan</span>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => zoom(-STEP)} disabled={scale === MIN_SCALE} aria-label="zoom out" className="w-10 h-10 rounded bg-white/20 disabled:opacity-40 text-2xl">−</button>
          <button type="button" onClick={() => zoom(STEP)} disabled={scale === MAX_SCALE} aria-label="zoom in" className="w-10 h-10 rounded bg-white/20 disabled:opacity-40 text-2xl">+</button>
          <button type="button" onClick={reset} aria-label="reset photo" className="px-3 h-10 rounded bg-white/20 text-sm">Reset</button>
          {!embedded && <button type="button" onClick={onClose} aria-label="close photo" className="w-10 h-10 rounded bg-white/20 text-2xl">✕</button>}
        </div>
      </div>
      <div
        ref={scrollRef}
        className="flex-1 min-h-0 overflow-auto"
        role="region"
        aria-label="Pan scorecard photo"
        tabIndex={0}
        style={{ cursor: 'grab' }}
        onPointerDown={(event) => {
          // Touch uses native scrolling, including momentum on phones.
          if (event.pointerType !== 'mouse' || event.button !== 0) return;
          drag.current = { x: event.clientX, y: event.clientY, left: event.currentTarget.scrollLeft, top: event.currentTarget.scrollTop };
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!drag.current) return;
          event.currentTarget.scrollLeft = drag.current.left + drag.current.x - event.clientX;
          event.currentTarget.scrollTop = drag.current.top + drag.current.y - event.clientY;
        }}
        onPointerUp={() => { drag.current = null; }}
        onPointerCancel={() => { drag.current = null; }}
        onLostPointerCapture={() => { drag.current = null; }}
      >
        <img
          src={src}
          alt="scorecard"
          onLoad={() => {
            if (!embedded && scrollRef.current) scrollRef.current.scrollLeft = scrollRef.current.scrollWidth;
            onLoad?.();
          }}
          onError={onError}
          style={{ width: `${scale * 100}%`, maxWidth: 'none' }}
          className="block select-none"
          draggable={false}
        />
      </div>
    </div>
  );
};

export default ScorecardPhotoZoom;
