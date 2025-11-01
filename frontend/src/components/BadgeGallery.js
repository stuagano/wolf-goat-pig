import React, { useState, useEffect } from 'react';
import './BadgeGallery.css';

const RARITY_COLORS = {
  common: '#9CA3AF',
  rare: '#3B82F6',
  epic: '#A855F7',
  legendary: '#F59E0B',
  mythic: '#EC4899'
};

const CATEGORY_LABELS = {
  achievement: 'Achievement',
  progression: 'Progression',
  seasonal: 'Seasonal',
  rare_event: 'Rare Event',
  collectible_series: 'Series'
};

const BadgeGallery = ({ playerId }) => {
  const [earnedBadges, setEarnedBadges] = useState([]);
  const [allBadges, setAllBadges] = useState([]);
  const [badgeStats, setBadgeStats] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [selectedBadge, setSelectedBadge] = useState(null);

  useEffect(() => {
    fetchBadgeData();
  }, [playerId]);

  const fetchBadgeData = async () => {
    try {
      setLoading(true);

      // Fetch earned badges
      const earnedResponse = await fetch(`/api/badges/player/${playerId}/earned`);
      const earnedData = await earnedResponse.json();
      setEarnedBadges(earnedData);

      // Fetch all available badges
      const allResponse = await fetch('/api/badges/available');
      const allData = await allResponse.json();
      setAllBadges(allData);

      // Fetch badge stats
      const statsResponse = await fetch(`/api/badges/player/${playerId}/stats`);
      const statsData = await statsResponse.json();
      setBadgeStats(statsData);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching badge data:', error);
      setLoading(false);
    }
  };

  const getBadgeRarityClass = (rarity) => {
    return `badge-rarity-${rarity}`;
  };

  const hasBadge = (badgeId) => {
    return earnedBadges.some(eb => eb.badge.badge_id === badgeId);
  };

  const getEarnedBadgeData = (badgeId) => {
    return earnedBadges.find(eb => eb.badge.badge_id === badgeId);
  };

  const filterBadges = () => {
    let filtered = allBadges;

    if (activeFilter === 'earned') {
      filtered = allBadges.filter(b => hasBadge(b.badge_id));
    } else if (activeFilter === 'locked') {
      filtered = allBadges.filter(b => !hasBadge(b.badge_id));
    } else if (activeFilter !== 'all') {
      filtered = allBadges.filter(b => b.category === activeFilter);
    }

    return filtered;
  };

  const BadgeCard = ({ badge }) => {
    const earned = hasBadge(badge.badge_id);
    const earnedData = getEarnedBadgeData(badge.badge_id);

    return (
      <div
        className={`badge-card ${getBadgeRarityClass(badge.rarity)} ${!earned ? 'locked' : ''}`}
        onClick={() => setSelectedBadge({ ...badge, earned, earnedData })}
      >
        <div className="badge-image-container">
          {earned ? (
            <img
              src={badge.image_url || '/badges/placeholder.png'}
              alt={badge.name}
              className="badge-image"
            />
          ) : (
            <div className="badge-locked">
              <span className="lock-icon">🔒</span>
            </div>
          )}
          {earned && earnedData && (
            <div className="badge-serial">#{earnedData.serial_number}</div>
          )}
        </div>

        <div className="badge-info">
          <h4 className="badge-name">{badge.name}</h4>
          <span className={`badge-rarity-label ${badge.rarity}`}>
            {badge.rarity.toUpperCase()}
          </span>
        </div>

        {badge.max_supply && (
          <div className="badge-supply">
            {badge.current_supply} / {badge.max_supply}
          </div>
        )}
      </div>
    );
  };

  const BadgeModal = () => {
    if (!selectedBadge) return null;

    return (
      <div className="badge-modal-overlay" onClick={() => setSelectedBadge(null)}>
        <div className="badge-modal" onClick={(e) => e.stopPropagation()}>
          <button className="modal-close" onClick={() => setSelectedBadge(null)}>×</button>

          <div className={`modal-header ${getBadgeRarityClass(selectedBadge.rarity)}`}>
            <div className="modal-badge-image">
              {selectedBadge.earned ? (
                <img
                  src={selectedBadge.image_url || '/badges/placeholder.png'}
                  alt={selectedBadge.name}
                />
              ) : (
                <div className="badge-locked-large">
                  <span className="lock-icon">🔒</span>
                </div>
              )}
            </div>
            <div className="modal-badge-title">
              <h2>{selectedBadge.name}</h2>
              <span className={`badge-rarity-label ${selectedBadge.rarity}`}>
                {selectedBadge.rarity.toUpperCase()}
              </span>
            </div>
          </div>

          <div className="modal-body">
            <p className="badge-description">{selectedBadge.description}</p>

            {selectedBadge.earned && selectedBadge.earnedData && (
              <div className="earned-info">
                <div className="earned-stat">
                  <span className="stat-label">Serial Number</span>
                  <span className="stat-value">#{selectedBadge.earnedData.serial_number}</span>
                </div>
                <div className="earned-stat">
                  <span className="stat-label">Earned On</span>
                  <span className="stat-value">
                    {new Date(selectedBadge.earnedData.earned_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            )}

            <div className="badge-metadata">
              <div className="metadata-item">
                <span className="metadata-label">Category</span>
                <span className="metadata-value">
                  {CATEGORY_LABELS[selectedBadge.category] || selectedBadge.category}
                </span>
              </div>

              {selectedBadge.max_supply && (
                <div className="metadata-item">
                  <span className="metadata-label">Supply</span>
                  <span className="metadata-value">
                    {selectedBadge.current_supply} / {selectedBadge.max_supply}
                  </span>
                </div>
              )}

              {selectedBadge.points_value > 0 && (
                <div className="metadata-item">
                  <span className="metadata-label">Points</span>
                  <span className="metadata-value">{selectedBadge.points_value} pts</span>
                </div>
              )}
            </div>

            {!selectedBadge.earned && (
              <div className="unlock-hint">
                <p>🔐 This badge is locked. Complete the challenge to unlock!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="badge-gallery loading">
        <div className="spinner">Loading badges...</div>
      </div>
    );
  }

  const filteredBadges = filterBadges();

  return (
    <div className="badge-gallery">
      <div className="gallery-header">
        <h2>🏆 Badge Collection</h2>

        {badgeStats && (
          <div className="badge-stats-summary">
            <div className="stat-box">
              <span className="stat-number">{badgeStats.total_earned}</span>
              <span className="stat-label">Earned</span>
            </div>
            <div className="stat-box">
              <span className="stat-number">{badgeStats.total_available}</span>
              <span className="stat-label">Available</span>
            </div>
            <div className="stat-box">
              <span className="stat-number">{badgeStats.completion_percentage.toFixed(1)}%</span>
              <span className="stat-label">Complete</span>
            </div>
          </div>
        )}
      </div>

      <div className="gallery-filters">
        <button
          className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => setActiveFilter('all')}
        >
          All Badges
        </button>
        <button
          className={`filter-btn ${activeFilter === 'earned' ? 'active' : ''}`}
          onClick={() => setActiveFilter('earned')}
        >
          Earned ({earnedBadges.length})
        </button>
        <button
          className={`filter-btn ${activeFilter === 'locked' ? 'active' : ''}`}
          onClick={() => setActiveFilter('locked')}
        >
          Locked ({allBadges.length - earnedBadges.length})
        </button>
        <button
          className={`filter-btn ${activeFilter === 'achievement' ? 'active' : ''}`}
          onClick={() => setActiveFilter('achievement')}
        >
          Achievements
        </button>
        <button
          className={`filter-btn ${activeFilter === 'progression' ? 'active' : ''}`}
          onClick={() => setActiveFilter('progression')}
        >
          Progression
        </button>
        <button
          className={`filter-btn ${activeFilter === 'collectible_series' ? 'active' : ''}`}
          onClick={() => setActiveFilter('collectible_series')}
        >
          Series
        </button>
      </div>

      <div className="badge-grid">
        {filteredBadges.map((badge) => (
          <BadgeCard key={badge.badge_id} badge={badge} />
        ))}
      </div>

      {filteredBadges.length === 0 && (
        <div className="no-badges">
          <p>No badges found matching your filter.</p>
        </div>
      )}

      {selectedBadge && <BadgeModal />}
    </div>
  );
};

export default BadgeGallery;
