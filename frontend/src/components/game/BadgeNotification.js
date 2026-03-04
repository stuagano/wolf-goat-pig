import React, { useState, useEffect, useCallback } from 'react';
import './BadgeNotification.css';

/**
 * BadgeNotification - Celebratory popup when player earns a badge
 * Shows animated badge reveal with confetti effect for rare badges
 */
const BadgeNotification = ({ badge, onClose }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);

  const handleClose = useCallback(() => {
    setIsVisible(false);
    setTimeout(() => {
      if (onClose) onClose();
    }, 300);
  }, [onClose]);

  useEffect(() => {
    // Trigger entrance animation
    setTimeout(() => setIsVisible(true), 100);

    // Show confetti for epic+ badges
    if (['epic', 'legendary', 'mythic'].includes(badge.rarity)) {
      setTimeout(() => setShowConfetti(true), 500);
    }

    // Auto-close after 5 seconds
    const timer = setTimeout(() => {
      handleClose();
    }, 5000);

    return () => clearTimeout(timer);
  }, [badge, handleClose]);

  const getRarityEmoji = (rarity) => {
    const emojis = {
      common: '🎖️',
      rare: '🏅',
      epic: '🏆',
      legendary: '👑',
      mythic: '⭐'
    };
    return emojis[rarity] || '🎖️';
  };

  const getSuccessMessage = (rarity) => {
    const messages = {
      common: 'Badge Unlocked!',
      rare: 'Rare Achievement!',
      epic: 'Epic Achievement Unlocked!',
      legendary: 'Legendary Achievement!',
      mythic: 'MYTHIC ACHIEVEMENT!'
    };
    return messages[rarity] || 'Badge Unlocked!';
  };

  return (
    <div className={`badge-notification-overlay ${isVisible ? 'visible' : ''}`}>
      {showConfetti && <Confetti />}

      <div className={`badge-notification-card ${badge.rarity} ${isVisible ? 'visible' : ''}`}>
        <button className="notification-close" onClick={handleClose}>×</button>

        <div className="notification-header">
          <div className="success-emoji">{getRarityEmoji(badge.rarity)}</div>
          <h2 className="success-message">{getSuccessMessage(badge.rarity)}</h2>
        </div>

        <div className="notification-badge-container">
          <div className={`badge-reveal ${badge.rarity}`}>
            <img
              src={badge.image_url || '/badges/placeholder.png'}
              alt={badge.name}
              className="badge-reveal-image"
            />
            {badge.serial_number && (
              <div className="badge-reveal-serial">
                #{badge.serial_number}
              </div>
            )}
          </div>
        </div>

        <div className="notification-details">
          <h3 className="badge-notification-name">{badge.name}</h3>
          <p className="badge-notification-description">{badge.description}</p>

          <div className={`rarity-badge ${badge.rarity}`}>
            {badge.rarity.toUpperCase()}
          </div>

          {badge.points_value > 0 && (
            <div className="points-earned">
              +{badge.points_value} points
            </div>
          )}
        </div>

        <div className="notification-actions">
          <button className="view-badge-btn" onClick={handleClose}>
            View Collection
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Confetti animation for rare badge unlocks
 */
const Confetti = () => {
  const confettiPieces = Array.from({ length: 50 }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 0.5,
    duration: 2 + Math.random() * 2,
    color: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'][Math.floor(Math.random() * 5)]
  }));

  return (
    <div className="confetti-container">
      {confettiPieces.map((piece) => (
        <div
          key={piece.id}
          className="confetti-piece"
          style={{
            left: `${piece.left}%`,
            animationDelay: `${piece.delay}s`,
            animationDuration: `${piece.duration}s`,
            backgroundColor: piece.color
          }}
        />
      ))}
    </div>
  );
};

/**
 * BadgeNotificationManager - Manages queue of badge notifications
 * Use this component at app root level to show notifications globally
 */
export const BadgeNotificationManager = () => {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    // Listen for badge earned events
    const handleBadgeEarned = (event) => {
      const badge = event.detail;
      setNotifications((prev) => [...prev, { id: Date.now(), badge }]);
    };

    window.addEventListener('badgeEarned', handleBadgeEarned);

    return () => {
      window.removeEventListener('badgeEarned', handleBadgeEarned);
    };
  }, []);

  const handleClose = (id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  if (notifications.length === 0) return null;

  // Show only the most recent notification
  const current = notifications[notifications.length - 1];

  return (
    <BadgeNotification
      badge={current.badge}
      onClose={() => handleClose(current.id)}
    />
  );
};

/**
 * Helper function to trigger badge notification from anywhere in the app
 * Usage: triggerBadgeNotification(badgeData)
 */
export const triggerBadgeNotification = (badge) => {
  const event = new CustomEvent('badgeEarned', { detail: badge });
  window.dispatchEvent(event);
};

export default BadgeNotification;
