import React from 'react';
import UnifiedGameInterface from './UnifiedGameInterface';

/**
 * @deprecated This component has been consolidated into UnifiedGameInterface.
 * Use <UnifiedGameInterface mode="regular" /> instead.
 */
const LegacyWolfGoatPigGame = (props) => {
  console.warn(
    'WolfGoatPigGame is deprecated. Use UnifiedGameInterface with mode="regular" instead.'
  );
  
  return <UnifiedGameInterface mode="regular" {...props} />;
};

export default LegacyWolfGoatPigGame;