// frontend/src/components/simulation/visual/ProbabilityBar.jsx
import React from 'react';
import PropTypes from 'prop-types';

/**
 * Visual probability bar component
 * Displays probability as a series of filled/unfilled dots
 */
const ProbabilityBar = ({ value }) => {
  // Clamp value between 0 and 1
  const clampedValue = Math.max(0, Math.min(1, value));
  const totalDots = 8;
  const filledDots = Math.round(clampedValue * totalDots);

  return (
    <div className="probability-bar">
      {Array.from({ length: totalDots }).map((_, index) => (
        <div
          key={index}
          className={`probability-dot ${index < filledDots ? 'filled' : ''}`}
        />
      ))}
    </div>
  );
};

ProbabilityBar.propTypes = {
  value: PropTypes.number.isRequired
};

export default ProbabilityBar;
