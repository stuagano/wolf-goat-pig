import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const GameBanner = () => {
  const [banner, setBanner] = useState(null);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    fetchBanner();
  }, []);

  const fetchBanner = async () => {
    try {
      const response = await fetch(`${API_URL}/banner`);
      if (response.ok) {
        const data = await response.json();
        if (data.banner) {
          // Check if user has dismissed this banner
          const dismissedBannerId = localStorage.getItem('dismissedBannerId');
          if (data.banner.dismissible && dismissedBannerId === String(data.banner.id)) {
            setIsDismissed(true);
          } else {
            setBanner(data.banner);
            setIsDismissed(false);
          }
        }
      }
    } catch (error) {
      console.error('Error fetching banner:', error);
    }
  };

  const handleDismiss = () => {
    if (banner && banner.dismissible) {
      localStorage.setItem('dismissedBannerId', String(banner.id));
      setIsDismissed(true);
    }
  };

  // Don't render if no banner or dismissed
  if (!banner || isDismissed) {
    return null;
  }

  // Icon based on banner type
  const getIcon = () => {
    if (!banner.show_icon) return null;

    const iconMap = {
      info: '📢',
      warning: '⚠️',
      announcement: '🎉',
      rules: '📋'
    };

    return iconMap[banner.banner_type] || '📢';
  };

  return (
    <div
      style={{
        backgroundColor: banner.background_color,
        color: banner.text_color,
        padding: '16px 20px',
        borderRadius: '8px',
        marginBottom: '20px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'relative',
        animation: 'slideDown 0.3s ease-out'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
        {banner.show_icon && (
          <span
            style={{
              fontSize: '24px',
              marginRight: '12px',
              flexShrink: 0
            }}
          >
            {getIcon()}
          </span>
        )}
        <div style={{ flex: 1 }}>
          {banner.title && (
            <h3
              style={{
                margin: '0 0 4px 0',
                fontSize: '18px',
                fontWeight: 'bold',
                color: banner.text_color
              }}
            >
              {banner.title}
            </h3>
          )}
          <p
            style={{
              margin: 0,
              fontSize: '15px',
              lineHeight: '1.5',
              color: banner.text_color
            }}
          >
            {banner.message}
          </p>
        </div>
      </div>

      {banner.dismissible && (
        <button
          onClick={handleDismiss}
          style={{
            background: 'rgba(255, 255, 255, 0.2)',
            border: 'none',
            color: banner.text_color,
            fontSize: '20px',
            width: '30px',
            height: '30px',
            borderRadius: '50%',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginLeft: '12px',
            flexShrink: 0,
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
          }}
          aria-label="Dismiss banner"
        >
          ×
        </button>
      )}

      <style>
        {`
          @keyframes slideDown {
            from {
              opacity: 0;
              transform: translateY(-20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}
      </style>
    </div>
  );
};

export default GameBanner;
