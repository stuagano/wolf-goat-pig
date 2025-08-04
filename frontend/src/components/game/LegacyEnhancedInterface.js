import React from 'react';
import UnifiedGameInterface from './UnifiedGameInterface';

/**
 * @deprecated This component has been consolidated into UnifiedGameInterface.
 * Use <UnifiedGameInterface mode="enhanced" /> instead.
 */
const LegacyEnhancedInterface = (props) => {
  console.warn(
    'EnhancedWGPInterface is deprecated. Use UnifiedGameInterface with mode="enhanced" instead.'
  );
  
  return <UnifiedGameInterface mode="enhanced" {...props} />;
};

export default LegacyEnhancedInterface;