// frontend/src/components/simulation/visual/EducationalTooltip.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Tooltip, IconButton, Typography, Box } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';

/**
 * Educational tooltip component that provides contextual help
 * Shows an info icon button that displays detailed explanation on hover
 */
const EducationalTooltip = ({ title, content, placement = 'top' }) => {
  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            {title}
          </Typography>
          <Typography variant="body2">
            {content}
          </Typography>
        </Box>
      }
      arrow
      placement={placement}
    >
      <IconButton size="small" aria-label={title}>
        <InfoIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  );
};

EducationalTooltip.propTypes = {
  title: PropTypes.string.isRequired,
  content: PropTypes.string.isRequired,
  placement: PropTypes.oneOf([
    'bottom-end',
    'bottom-start',
    'bottom',
    'left-end',
    'left-start',
    'left',
    'right-end',
    'right-start',
    'right',
    'top-end',
    'top-start',
    'top'
  ])
};

export default EducationalTooltip;
