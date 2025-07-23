import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || "";

const WarmupMessage = ({ onReady, children }) => {
  const [isWarming, setIsWarming] = useState(true);
  const [attempts, setAttempts] = useState(0);
  const [message, setMessage] = useState("Reticulating splines...");
  const [dots, setDots] = useState("...");

  const warmupMessages = [
    "Reticulating splines...",
    "Calibrating golf physics...", 
    "Consulting the golf gods...",
    "Warming up the simulation engine...",
    "Loading course data...",
    "Preparing for epic golf battles...",
    "Initializing wolf, goat, and pig protocols...",
    "Shuffling the deck...",
    "Checking wind conditions...",
    "Polishing golf clubs..."
  ];

  useEffect(() => {
    let dotInterval;
    let messageInterval;
    let healthCheckInterval;

    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/health`, {
          method: 'GET',
          timeout: 5000,
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'healthy' || data.database === 'healthy') {
            setIsWarming(false);
            if (onReady) onReady();
            return;
          }
          if (data.message && data.message !== message) {
            setMessage(data.message);
          }
        }
      } catch (error) {
        console.log('Health check failed, backend still warming up:', error.message);
      }
      
      setAttempts(prev => prev + 1);
    };

    if (isWarming) {
      // Animate dots
      dotInterval = setInterval(() => {
        setDots(prev => prev.length >= 3 ? "." : prev + ".");
      }, 500);

      // Rotate messages every 3 seconds
      messageInterval = setInterval(() => {
        setMessage(warmupMessages[Math.floor(Math.random() * warmupMessages.length)]);
      }, 3000);

      // Check health every 2 seconds
      healthCheckInterval = setInterval(checkHealth, 2000);
      
      // Initial check
      checkHealth();
    }

    return () => {
      clearInterval(dotInterval);
      clearInterval(messageInterval);
      clearInterval(healthCheckInterval);
    };
  }, [isWarming, message, onReady]);

  if (!isWarming) {
    return children;
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(25, 118, 210, 0.95)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      color: 'white',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{
        textAlign: 'center',
        padding: '40px',
        borderRadius: '16px',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        maxWidth: '400px',
        margin: '20px'
      }}>
        <div style={{
          fontSize: '48px',
          marginBottom: '20px',
          animation: 'spin 2s linear infinite'
        }}>
          ⚙️
        </div>
        
        <style dangerouslySetInnerHTML={{
          __html: `
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `
        }} />
        
        <h2 style={{ 
          margin: '0 0 10px 0',
          fontSize: '24px',
          fontWeight: 'bold'
        }}>
          Wolf Goat Pig
        </h2>
        
        <div style={{
          fontSize: '18px',
          marginBottom: '20px',
          minHeight: '25px'
        }}>
          {message}{dots}
        </div>
        
        <div style={{
          fontSize: '14px',
          opacity: 0.8,
          fontStyle: 'italic'
        }}>
          Backend is warming up on Render's free tier
        </div>
        
        {attempts > 10 && (
          <div style={{
            fontSize: '12px',
            marginTop: '15px',
            padding: '10px',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            opacity: 0.9
          }}>
            This may take up to 50 seconds on the free tier.<br/>
            Thank you for your patience! 🏌️‍♂️
          </div>
        )}
      </div>
    </div>
  );
};

export default WarmupMessage;