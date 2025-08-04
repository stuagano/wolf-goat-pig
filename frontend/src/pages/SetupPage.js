import React from 'react';
import { useNavigate } from 'react-router-dom';
import { GameSetupForm } from '../components/game';

function SetupPage({ onSetup }) {
  const navigate = useNavigate();
  return (
    <GameSetupForm 
      onSetup={state => { 
        onSetup(state); 
        navigate('/game'); 
      }} 
    />
  );
}

export default SetupPage;