// frontend/src/components/game/scorekeeper/HoleNavigation.jsx
// Extracted from SimpleScorekeeper.jsx — Previous/next hole buttons + complete hole action
import React from "react";
import PropTypes from "prop-types";

/**
 * HoleNavigation — sticky bottom thumb zone with prev/next hole and complete/update button
 */
const HoleNavigation = ({
  currentHole,
  editingHole,
  submitting,
  holeHistory,
  jumpToHole,
  handleSubmitHole,
}) => {
  return (
    <div className="thumb-zone">
      <div className="thumb-zone-inner">
        {/* Previous Hole Navigation */}
        <button
          className="thumb-zone-nav"
          onClick={() => currentHole > 1 && jumpToHole(currentHole - 1)}
          disabled={currentHole <= 1}
          aria-label={`Go to hole ${currentHole - 1}`}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <span style={{ fontSize: "18px" }}>{"\u25C0"}</span>
            <span className="hole-num">
              {currentHole > 1 ? currentHole - 1 : ""}
            </span>
          </div>
        </button>

        {/* Primary Action - Complete/Update Hole.
            A round is 18 holes; past that (edit-complete mode parks currentHole
            at 19) there is no hole to complete, so disable the action. */}
        {(() => {
          const pastRound = !editingHole && currentHole > 18;
          return (
            <button
              data-testid="complete-hole-button"
              className={`thumb-zone-primary ${editingHole ? "editing" : ""}`}
              onClick={handleSubmitHole}
              disabled={submitting || pastRound}
            >
              {submitting
                ? "Submitting..."
                : editingHole
                  ? `Update Hole ${editingHole}`
                  : pastRound
                    ? "Round complete"
                    : `\u2713 Complete Hole ${currentHole}`}
            </button>
          );
        })()}

        {/* Next Hole Navigation */}
        <button
          className="thumb-zone-nav"
          onClick={() => currentHole < 18 && jumpToHole(currentHole + 1)}
          disabled={
            currentHole >= 18 &&
            !holeHistory.find((h) => h.hole === currentHole + 1)
          }
          aria-label={`Go to hole ${currentHole + 1}`}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <span style={{ fontSize: "18px" }}>{"\u25B6"}</span>
            <span className="hole-num">
              {currentHole < 18 ? currentHole + 1 : ""}
            </span>
          </div>
        </button>
      </div>
    </div>
  );
};

HoleNavigation.propTypes = {
  currentHole: PropTypes.number.isRequired,
  editingHole: PropTypes.number,
  submitting: PropTypes.bool.isRequired,
  holeHistory: PropTypes.array.isRequired,
  jumpToHole: PropTypes.func.isRequired,
  handleSubmitHole: PropTypes.func.isRequired,
};

export default HoleNavigation;
