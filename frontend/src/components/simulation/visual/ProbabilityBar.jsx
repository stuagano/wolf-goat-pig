// frontend/src/components/simulation/visual/ProbabilityBar.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Box } from '@mui/material';

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
    <Box className="probability-bar">
      {Array.from({ length: totalDots }).map((_, index) => (
        <Box
          key={index}
          className={`probability-dot ${index < filledDots ? 'filled' : ''}`}
        />
      ))}
    </Box>
  );
};

ProbabilityBar.propTypes = {
  value: PropTypes.number.isRequired
};

export default ProbabilityBar;
