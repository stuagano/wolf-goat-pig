import React, { useState } from 'react';
import './MonteCarloSimulation.css';

const API_URL = process.env.REACT_APP_API_URL || '';

const MonteCarloSimulation = () => {
  const [formData, setFormData] = useState({
    humanPlayer: {
      id: 'human',
      name: 'Stuart',
      handicap: 10,
      is_human: true
    },
    computerPlayers: [
      { id: 'comp1', name: 'Tiger Bot', handicap: 2.0, personality: 'aggressive', is_human: false },
      { id: 'comp2', name: 'Strategic Sam', handicap: 8.5, personality: 'strategic', is_human: false },
      { id: 'comp3', name: 'Conservative Carl', handicap: 15.0, personality: 'conservative', is_human: false }
    ],
    numSimulations: 100,
    courseName: ''
  });

  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleHumanPlayerChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      humanPlayer: {
        ...prev.humanPlayer,
        [field]: value
      }
    }));
  };

  const handleComputerPlayerChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      computerPlayers: prev.computerPlayers.map((player, i) => 
        i === index ? { ...player, [field]: value } : player
      )
    }));
  };

  const runMonteCarloSimulation = async () => {
    setIsRunning(true);
    setError('');
    setResults(null);

    try {
      const response = await fetch(`${API_URL}/api/simulation/monte-carlo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          human_player: formData.humanPlayer,
          computer_players: formData.computerPlayers,
          num_simulations: formData.numSimulations,
          course_name: formData.courseName || null
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const formatScoreDistribution = (distribution) => {
    const entries = Object.entries(distribution).sort((a, b) => parseInt(b[0]) - parseInt(a[0]));
    return entries.slice(0, 5).map(([score, count]) => (
      <div key={score} className="score-entry">
        <span className="score">{score > 0 ? `+${score}` : score}</span>
        <span className="count">{count} times</span>
      </div>
    ));
  };

  return (
    <div className="monte-carlo-container">
      <h2>🎲 Monte Carlo Simulation</h2>
      <p className="description">
        Run multiple simulations to see statistical outcomes when playing against computer opponents.
        This will show you long-term performance expectations and help identify optimal strategies.
      </p>

      <div className="simulation-setup">
        <h3>Simulation Setup</h3>
        
        {/* Human Player Setup */}
        <div className="player-section">
          <h4>👤 Human Player</h4>
          <div className="form-row">
            <label>
              Name:
              <input
                type="text"
                value={formData.humanPlayer.name}
                onChange={(e) => handleHumanPlayerChange('name', e.target.value)}
              />
            </label>
            <label>
              Handicap:
              <input
                type="number"
                step="0.1"
                min="0"
                max="36"
                value={formData.humanPlayer.handicap}
                onChange={(e) => handleHumanPlayerChange('handicap', parseFloat(e.target.value))}
              />
            </label>
          </div>
        </div>

        {/* Computer Players Setup */}
        <div className="player-section">
          <h4>🤖 Computer Opponents</h4>
          {formData.computerPlayers.map((player, index) => (
            <div key={index} className="computer-player-row">
              <label>
                Name:
                <input
                  type="text"
                  value={player.name}
                  onChange={(e) => handleComputerPlayerChange(index, 'name', e.target.value)}
                />
              </label>
              <label>
                Handicap:
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="36"
                  value={player.handicap}
                  onChange={(e) => handleComputerPlayerChange(index, 'handicap', parseFloat(e.target.value))}
                />
              </label>
              <label>
                Personality:
                <select
                  value={player.personality}
                  onChange={(e) => handleComputerPlayerChange(index, 'personality', e.target.value)}
                >
                  <option value="aggressive">Aggressive</option>
                  <option value="conservative">Conservative</option>
                  <option value="strategic">Strategic</option>
                  <option value="balanced">Balanced</option>
                </select>
              </label>
            </div>
          ))}
        </div>

        {/* Simulation Parameters */}
        <div className="simulation-params">
          <h4>⚙️ Simulation Parameters</h4>
          <div className="form-row">
            <label>
              Number of Games:
              <input
                type="number"
                min="10"
                max="1000"
                value={formData.numSimulations}
                onChange={(e) => handleInputChange('numSimulations', parseInt(e.target.value))}
              />
            </label>
            <label>
              Course (optional):
              <input
                type="text"
                placeholder="Leave blank for standard course"
                value={formData.courseName}
                onChange={(e) => handleInputChange('courseName', e.target.value)}
              />
            </label>
          </div>
        </div>

        <button 
          className="run-simulation-btn"
          onClick={runMonteCarloSimulation}
          disabled={isRunning}
        >
          {isRunning ? '🔄 Running Simulation...' : '🚀 Run Monte Carlo Simulation'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ❌ Error: {error}
        </div>
      )}

      {isRunning && (
        <div className="running-indicator">
          <div className="spinner"></div>
          <p>Running {formData.numSimulations} simulations...</p>
          <p>This may take a few moments...</p>
        </div>
      )}

      {results && (
        <div className="results-container">
          <h3>📊 Simulation Results</h3>
          
          {/* Key Insights */}
          <div className="insights-section">
            <h4>🎯 Key Insights</h4>
            <ul className="insights-list">
              {results.insights.map((insight, index) => (
                <li key={index}>{insight}</li>
              ))}
            </ul>
          </div>

          {/* Player Statistics */}
          <div className="player-stats-section">
            <h4>🏆 Player Statistics</h4>
            <div className="stats-grid">
              {Object.entries(results.summary.player_statistics).map(([playerId, stats]) => {
                const playerName = playerId === formData.humanPlayer.id 
                  ? formData.humanPlayer.name 
                  : formData.computerPlayers.find(p => p.id === playerId)?.name || playerId;
                
                return (
                  <div key={playerId} className={`player-stat-card ${playerId === formData.humanPlayer.id ? 'human-player' : ''}`}>
                    <h5>{playerName} {playerId === formData.humanPlayer.id ? '(You)' : ''}</h5>
                    <div className="stat-row">
                      <span className="stat-label">Wins:</span>
                      <span className="stat-value">{stats.wins} ({stats.win_percentage.toFixed(1)}%)</span>
                    </div>
                    <div className="stat-row">
                      <span className="stat-label">Avg Score:</span>
                      <span className="stat-value">{stats.average_score > 0 ? '+' : ''}{stats.average_score}</span>
                    </div>
                    <div className="stat-row">
                      <span className="stat-label">Best Game:</span>
                      <span className="stat-value">{stats.best_score > 0 ? '+' : ''}{stats.best_score}</span>
                    </div>
                    <div className="stat-row">
                      <span className="stat-label">Worst Game:</span>
                      <span className="stat-value">{stats.worst_score > 0 ? '+' : ''}{stats.worst_score}</span>
                    </div>
                    
                    <div className="score-distribution">
                      <h6>Top Scores:</h6>
                      {formatScoreDistribution(stats.score_distribution)}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Simulation Details */}
          <div className="simulation-details">
            <h4>📋 Simulation Details</h4>
            <div className="detail-row">
              <span>Total Games Played:</span>
              <span>{results.simulation_details.total_games}</span>
            </div>
            <div className="detail-row">
              <span>Course:</span>
              <span>{results.simulation_details.course}</span>
            </div>
            <div className="detail-row">
              <span>Human Player:</span>
              <span>{results.simulation_details.human_player}</span>
            </div>
            <div className="detail-row">
              <span>Opponents:</span>
              <span>{results.simulation_details.opponents.join(', ')}</span>
            </div>
          </div>

          {/* Strategic Recommendations */}
          <div className="recommendations-section">
            <h4>💡 Strategic Recommendations</h4>
            <div className="recommendations">
              {results.summary.player_statistics[formData.humanPlayer.id].win_percentage < 20 && (
                <div className="recommendation">
                  <strong>🎯 Focus on Partnership Selection:</strong> Try to partner with players closer to your handicap level for better team balance.
                </div>
              )}
              {results.summary.player_statistics[formData.humanPlayer.id].average_score < -2 && (
                <div className="recommendation">
                  <strong>🛡️ Play More Conservatively:</strong> Avoid going solo on difficult holes unless you have a significant stroke advantage.
                </div>
              )}
              {results.summary.player_statistics[formData.humanPlayer.id].win_percentage > 35 && (
                <div className="recommendation">
                  <strong>🚀 Great Performance:</strong> Your strategy is working well! Consider being slightly more aggressive on easier holes.
                </div>
              )}
              <div className="recommendation">
                <strong>📊 Sample Size:</strong> Run more simulations (500+) for more reliable statistical insights.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MonteCarloSimulation;