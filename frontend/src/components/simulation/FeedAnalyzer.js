import React, { useState } from 'react';

const FeedAnalyzer = () => {
  const [feedData, setFeedData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  
  // Golf validation rules
  const VALIDATION_RULES = {
    maxShotsPerHole: 15, // Reasonable maximum for amateur play
    maxDistanceFromPin: 600, // Yards
    validLieTypes: ['tee', 'fairway', 'rough', 'bunker', 'water', 'green'],
    validShotQualities: ['excellent', 'great', 'good', 'ok', 'poor', 'terrible'],
    parValues: [3, 4, 5], // Standard par values
    maxHandicap: 54 // USGA maximum
  };

  const analyzeFeed = (data) => {
    const results = {
      isValid: true,
      errors: [],
      warnings: [],
      golfMechanics: {},
      statistics: {},
      timeline: []
    };

    try {
      // Basic structure validation
      if (!data.players || !Array.isArray(data.players)) {
        results.errors.push('Missing or invalid players array');
        results.isValid = false;
      }

      if (!data.ballPositions) {
        results.errors.push('Missing ballPositions data');
        results.isValid = false;
      }

      if (!data.feedback || !Array.isArray(data.feedback)) {
        results.errors.push('Missing or invalid feedback array');
        results.isValid = false;
      }

      // Player validation
      if (data.players) {
        results.golfMechanics.playerCount = data.players.length;
        
        data.players.forEach((player, idx) => {
          if (!player.name) {
            results.errors.push(`Player ${idx + 1}: Missing name`);
          }
          
          if (typeof player.handicap !== 'number' || player.handicap < 0 || player.handicap > VALIDATION_RULES.maxHandicap) {
            results.errors.push(`Player ${player.name}: Invalid handicap ${player.handicap}`);
          }
        });
      }

      // Ball position validation
      if (data.ballPositions) {
        const positions = Object.entries(data.ballPositions);
        results.golfMechanics.ballPositions = {};
        
        positions.forEach(([playerId, position]) => {
          const playerName = data.players?.find(p => p.id === playerId)?.name || playerId;
          
          // Validate shot count
          if (position.shot_count > VALIDATION_RULES.maxShotsPerHole) {
            results.warnings.push(`${playerName}: High shot count (${position.shot_count})`);
          }
          
          // Validate distance
          if (position.distance_to_pin > VALIDATION_RULES.maxDistanceFromPin) {
            results.errors.push(`${playerName}: Unrealistic distance (${position.distance_to_pin}yd)`);
          }
          
          // Validate lie type
          if (!VALIDATION_RULES.validLieTypes.includes(position.lie_type)) {
            results.errors.push(`${playerName}: Invalid lie type '${position.lie_type}'`);
          }
          
          // Hole out validation
          if (position.holed && position.distance_to_pin !== 0) {
            results.errors.push(`${playerName}: Marked as holed but distance is ${position.distance_to_pin}yd`);
          }
          
          if (position.distance_to_pin === 0 && !position.holed) {
            results.warnings.push(`${playerName}: At pin (0yd) but not marked as holed`);
          }
          
          results.golfMechanics.ballPositions[playerName] = {
            shots: position.shot_count,
            distance: position.distance_to_pin,
            lie: position.lie_type,
            finished: position.holed
          };
        });
      }

      // Feedback sequence validation (contains shot data)
      if (data.feedback) {
        let shotCount = 0;
        let lastShotNumber = 0;
        const playerShotCounts = {};
        const shotQualities = [];
        
        data.feedback.forEach((feedbackItem, idx) => {
          if (typeof feedbackItem === 'string') {
            // Parse JSON embedded in feedback strings
            if (feedbackItem.includes('shot_result')) {
              try {
                const jsonMatch = feedbackItem.match(/\{.*\}/);
                if (jsonMatch) {
                  const shotData = JSON.parse(jsonMatch[0]);
                  
                  if (shotData.shot_result) {
                    shotCount++;
                    const shot = shotData.shot_result;
                    
                    // Track player shots
                    const playerId = shot.player_id;
                    playerShotCounts[playerId] = (playerShotCounts[playerId] || 0) + 1;
                    
                    // Validate shot quality
                    if (shot.shot_quality && !VALIDATION_RULES.validShotQualities.includes(shot.shot_quality)) {
                      results.warnings.push(`Feedback ${idx + 1}: Invalid shot quality '${shot.shot_quality}'`);
                    }
                    
                    if (shot.shot_quality) {
                      shotQualities.push(shot.shot_quality);
                    }
                    
                    // Distance validation
                    if (shot.distance_to_pin > VALIDATION_RULES.maxDistanceFromPin) {
                      results.warnings.push(`Feedback ${idx + 1}: Unrealistic shot distance (${shot.distance_to_pin}yd)`);
                    }
                    
                    // Hole out validation
                    if (shot.made_shot && shot.distance_to_pin !== 0) {
                      results.warnings.push(`Feedback ${idx + 1}: Shot marked as made but distance is ${shot.distance_to_pin}yd`);
                    }
                  }
                }
              } catch (e) {
                results.warnings.push(`Feedback ${idx + 1}: Failed to parse shot data JSON`);
              }
            }
          }
        });
        
        results.golfMechanics.totalShots = shotCount;
        results.golfMechanics.playerShotCounts = playerShotCounts;
        results.golfMechanics.shotQualities = shotQualities;
        
        // Use current shot if available
        if (data.currentShot) {
          results.golfMechanics.currentShot = data.currentShot;
        }
        
        // Check for reasonable shot distribution
        const avgShots = shotCount / (data.players?.length || 1);
        if (avgShots > 10) {
          results.warnings.push(`High average shot count per player: ${avgShots.toFixed(1)}`);
        }
      }

      // Hole-specific validation
      if (data.par && !VALIDATION_RULES.parValues.includes(data.par)) {
        results.errors.push(`Invalid par value: ${data.par}`);
      }
      
      // Statistics calculation
      results.statistics = calculateStatistics(data);
      
      // Generate timeline
      results.timeline = generateTimeline(data);

    } catch (err) {
      results.errors.push(`Analysis error: ${err.message}`);
      results.isValid = false;
    }

    return results;
  };

  const calculateStatistics = (data) => {
    const stats = {
      averageShots: 0,
      completionRate: 0,
      shotQualityDistribution: {},
      lieTypeDistribution: {},
      playerPerformance: {}
    };

    if (data.ballPositions) {
      const positions = Object.values(data.ballPositions);
      stats.averageShots = positions.reduce((sum, pos) => sum + pos.shot_count, 0) / positions.length;
      stats.completionRate = positions.filter(pos => pos.holed).length / positions.length * 100;
      
      // Lie type distribution
      positions.forEach(pos => {
        stats.lieTypeDistribution[pos.lie_type] = (stats.lieTypeDistribution[pos.lie_type] || 0) + 1;
      });
    }

    if (data.feedback) {
      // Shot quality distribution from feedback
      data.feedback.forEach(feedbackItem => {
        if (typeof feedbackItem === 'string' && feedbackItem.includes('shot_result')) {
          try {
            const jsonMatch = feedbackItem.match(/\{.*\}/);
            if (jsonMatch) {
              const shotData = JSON.parse(jsonMatch[0]);
              if (shotData.shot_result && shotData.shot_result.shot_quality) {
                const quality = shotData.shot_result.shot_quality;
                stats.shotQualityDistribution[quality] = (stats.shotQualityDistribution[quality] || 0) + 1;
              }
            }
          } catch (e) {
            // Ignore JSON parsing errors
          }
        }
      });
    }

    return stats;
  };

  const generateTimeline = (data) => {
    if (!data.feedback) return [];
    
    const timeline = [];
    
    data.feedback.forEach((feedbackItem, idx) => {
      if (typeof feedbackItem === 'string' && feedbackItem.includes('shot_result')) {
        try {
          const jsonMatch = feedbackItem.match(/\{.*\}/);
          if (jsonMatch) {
            const shotData = JSON.parse(jsonMatch[0]);
            if (shotData.shot_result) {
              const shot = shotData.shot_result;
              timeline.push({
                shot: shot.shot_number,
                player: data.players?.find(p => p.id === shot.player_id)?.name || shot.player_id,
                quality: shot.shot_quality,
                distance: shot.distance_to_pin,
                lie: shot.lie_type
              });
            }
          }
        } catch (e) {
          // Ignore JSON parsing errors
        }
      }
    });
    
    return timeline.slice(-10); // Last 10 shots
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        setFeedData(data);
        setError(null);
        
        // Perform analysis
        const analysisResults = analyzeFeed(data);
        setAnalysis(analysisResults);
      } catch (err) {
        setError(`Failed to parse JSON: ${err.message}`);
        setFeedData(null);
        setAnalysis(null);
      }
    };
    
    reader.readAsText(file);
  };

  const renderValidationResults = () => {
    if (!analysis) return null;

    return (
      <div style={{ marginTop: 20 }}>
        <div style={{ 
          padding: 16, 
          borderRadius: 8, 
          backgroundColor: analysis.isValid ? '#d4edda' : '#f8d7da',
          border: `1px solid ${analysis.isValid ? '#c3e6cb' : '#f5c6cb'}`,
          marginBottom: 16
        }}>
          <h3 style={{ margin: '0 0 8px 0', color: analysis.isValid ? '#155724' : '#721c24' }}>
            {analysis.isValid ? '✅ Feed is Valid' : '❌ Feed has Issues'}
          </h3>
        </div>

        {analysis.errors.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <h4 style={{ color: '#dc3545' }}>Errors ({analysis.errors.length})</h4>
            <ul style={{ color: '#721c24', backgroundColor: '#f8d7da', padding: 12, borderRadius: 4 }}>
              {analysis.errors.map((error, idx) => (
                <li key={idx}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {analysis.warnings.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <h4 style={{ color: '#856404' }}>Warnings ({analysis.warnings.length})</h4>
            <ul style={{ color: '#856404', backgroundColor: '#fff3cd', padding: 12, borderRadius: 4 }}>
              {analysis.warnings.map((warning, idx) => (
                <li key={idx}>{warning}</li>
              ))}
            </ul>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div style={{ padding: 16, border: '1px solid #dee2e6', borderRadius: 8 }}>
            <h4>Golf Mechanics</h4>
            <ul>
              <li>Players: {analysis.golfMechanics.playerCount}</li>
              <li>Total Shots: {analysis.golfMechanics.totalShots}</li>
              <li>Avg Shots/Player: {(analysis.golfMechanics.totalShots / (analysis.golfMechanics.playerCount || 1)).toFixed(1)}</li>
            </ul>
            
            {analysis.golfMechanics.ballPositions && (
              <div>
                <h5>Final Positions:</h5>
                {Object.entries(analysis.golfMechanics.ballPositions).map(([player, pos]) => (
                  <div key={player} style={{ fontSize: 14, marginBottom: 4 }}>
                    <strong>{player}</strong>: {pos.shots} shots, {pos.distance.toFixed(0)}yd, {pos.lie}
                    {pos.finished && <span style={{ color: 'green' }}> ✅ HOLED</span>}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ padding: 16, border: '1px solid #dee2e6', borderRadius: 8 }}>
            <h4>Statistics</h4>
            <ul>
              <li>Avg Shots: {analysis.statistics.averageShots?.toFixed(1)}</li>
              <li>Completion: {analysis.statistics.completionRate?.toFixed(0)}%</li>
            </ul>
            
            {Object.keys(analysis.statistics.shotQualityDistribution).length > 0 && (
              <div>
                <h5>Shot Quality:</h5>
                {Object.entries(analysis.statistics.shotQualityDistribution).map(([quality, count]) => (
                  <div key={quality} style={{ fontSize: 14 }}>
                    {quality}: {count}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {analysis.timeline.length > 0 && (
          <div style={{ padding: 16, border: '1px solid #dee2e6', borderRadius: 8 }}>
            <h4>Recent Shot Timeline</h4>
            <div style={{ maxHeight: 200, overflowY: 'auto' }}>
              {analysis.timeline.map((shot, idx) => (
                <div key={idx} style={{ 
                  padding: 8, 
                  borderBottom: '1px solid #eee',
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: 14
                }}>
                  <span><strong>Shot #{shot.shot}</strong> - {shot.player}</span>
                  <span>{shot.quality} → {shot.distance?.toFixed(0)}yd ({shot.lie})</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ padding: 20, maxWidth: 1000, margin: '0 auto' }}>
      <h2>🔍 Golf Feed Analyzer</h2>
      <p>Upload a game feed JSON file to analyze its correctness and golf mechanics.</p>
      
      <div style={{ marginBottom: 20 }}>
        <input
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          style={{ padding: 8, marginRight: 12 }}
        />
        <span style={{ fontSize: 14, color: '#666' }}>
          Select a JSON feed file exported from the simulation
        </span>
      </div>

      {error && (
        <div style={{ 
          color: '#721c24', 
          backgroundColor: '#f8d7da', 
          padding: 12, 
          borderRadius: 4, 
          marginBottom: 16,
          border: '1px solid #f5c6cb'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {feedData && (
        <div style={{ marginBottom: 20 }}>
          <h3>Feed Overview</h3>
          <div style={{ 
            backgroundColor: '#f8f9fa', 
            padding: 16, 
            borderRadius: 8, 
            border: '1px solid #dee2e6' 
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              <div><strong>Timestamp:</strong> {new Date(feedData.timestamp).toLocaleString()}</div>
              <div><strong>Hole:</strong> {feedData.hole} (Par {feedData.par})</div>
              <div><strong>Players:</strong> {feedData.players?.length || 0}</div>
              <div><strong>Feedback:</strong> {feedData.feedback?.length || 0}</div>
            </div>
          </div>
        </div>
      )}

      {renderValidationResults()}
    </div>
  );
};

export default FeedAnalyzer;