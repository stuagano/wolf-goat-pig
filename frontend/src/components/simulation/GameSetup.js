import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';
import { Button, Card, Input, Select } from '../ui';

const API_URL = process.env.REACT_APP_API_URL || "";

const GameSetup = ({
  humanPlayer,
  setHumanPlayer,
  computerPlayers,
  setComputerPlayers,
  selectedCourse,
  setSelectedCourse,
  courses,
  setCourses,
  personalities = [],
  setPersonalities,
  suggestedOpponents = [],
  setSuggestedOpponents,
  onStartGame
}) => {
  const theme = useTheme();
  
  // GHIN lookup modal state
  const [ghinLookupSlot, setGhinLookupSlot] = useState(null);
  const [ghinLookupFirstName, setGhinLookupFirstName] = useState("");
  const [ghinLookupLastName, setGhinLookupLastName] = useState("");
  const [ghinLookupResults, setGhinLookupResults] = useState([]);
  const [ghinLookupLoading, setGhinLookupLoading] = useState(false);
  const [ghinLookupError, setGhinLookupError] = useState("");

  useEffect(() => {
    // Fetch courses with error handling
    fetch(`${API_URL}/courses`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        if (!data || typeof data !== 'object') {
          throw new Error('Invalid courses data format');
        }
        setCourses(data);
        
        // Auto-select first course if none selected
        if (!selectedCourse && Object.keys(data).length > 0) {
          setSelectedCourse(Object.keys(data)[0]);
        }
      })
      .catch(error => {
        console.error('Failed to load courses:', error);
        
        // Provide fallback courses so game can still start
        const fallbackCourses = {
          "Default Course": {
            name: "Default Course",
            holes: Array.from({length: 18}, (_, i) => ({
              hole_number: i + 1,
              par: 4,
              yards: 400,
              stroke_index: i + 1,
              description: `Hole ${i + 1}`
            })),
            total_par: 72,
            total_yards: 7200,
            hole_count: 18
          }
        };
        
        setCourses(fallbackCourses);
        setSelectedCourse("Default Course");
        
        // Show user-friendly error message but don't block the game
        alert('Unable to load courses from server. Using default course to continue the game.');
      });
    
    // Fetch personalities with error handling
    fetch(`${API_URL}/personalities`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        if (Array.isArray(data)) {
          setPersonalities(data);
        } else {
          throw new Error('Invalid personalities data format');
        }
      })
      .catch(error => {
        console.error('Failed to load personalities:', error);
        // Provide fallback personalities
        const fallbackPersonalities = [
          { id: 'aggressive', name: 'Aggressive' },
          { id: 'conservative', name: 'Conservative' },
          { id: 'balanced', name: 'Balanced' }
        ];
        setPersonalities(fallbackPersonalities);
      });
    
    // Fetch suggested opponents with error handling
    fetch(`${API_URL}/suggested_opponents`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then(data => {
        if (Array.isArray(data)) {
          setSuggestedOpponents(data);
        } else {
          throw new Error('Invalid suggested opponents data format');
        }
      })
      .catch(error => {
        console.error('Failed to load suggested opponents:', error);
        // Provide fallback suggested opponents
        const fallbackOpponents = [
          { name: 'Bob', handicap: '12', personality: 'aggressive' },
          { name: 'Alice', handicap: '8', personality: 'conservative' },
          { name: 'Charlie', handicap: '16', personality: 'balanced' }
        ];
        setSuggestedOpponents(fallbackOpponents);
      });
  }, [setCourses, setPersonalities, setSuggestedOpponents, selectedCourse, setSelectedCourse]);

  // Initialize computer players if empty
  useEffect(() => {
    if (computerPlayers.length === 0) {
      setComputerPlayers([
        { id: "comp1", name: "", handicap: "", personality: "", is_human: false },
        { id: "comp2", name: "", handicap: "", personality: "", is_human: false },
        { id: "comp3", name: "", handicap: "", personality: "", is_human: false }
      ]);
    }
  }, [computerPlayers, setComputerPlayers]);

  const openGhinLookup = (slot) => {
    setGhinLookupSlot(slot);
    setGhinLookupFirstName("");
    setGhinLookupLastName("");
    setGhinLookupResults([]);
    setGhinLookupLoading(false);
    setGhinLookupError("");
  };

  const closeGhinLookup = () => {
    setGhinLookupSlot(null);
  };

  const doGhinLookup = async () => {
    if (!ghinLookupLastName.trim()) {
      setGhinLookupError("Last name required");
      return;
    }
    setGhinLookupLoading(true);
    setGhinLookupError("");
    setGhinLookupResults([]);
    try {
      const params = new URLSearchParams({ 
        last_name: ghinLookupLastName, 
        first_name: ghinLookupFirstName 
      });
      const res = await fetch(`${API_URL}/ghin/lookup?${params.toString()}`);
      if (!res.ok) throw new Error("Lookup failed");
      const data = await res.json();
      setGhinLookupResults(data);
      if (data.length === 0) setGhinLookupError("No golfers found");
    } catch (err) {
      setGhinLookupError("Lookup failed");
    } finally {
      setGhinLookupLoading(false);
    }
  };

  const selectGhinGolfer = (golfer) => {
    if (ghinLookupSlot === "human") {
      setHumanPlayer(h => ({ ...h, name: golfer.name, handicap: golfer.handicap || "", is_human: true }));
    } else {
      setComputerPlayers(players => players.map((p, i) => {
        const slotId = `comp${i+1}`;
        return slotId === ghinLookupSlot ? { ...p, name: golfer.name, handicap: golfer.handicap || "", is_human: false } : p;
      }));
    }
    closeGhinLookup();
  };

  const loadSuggestedOpponent = (opponentData, index) => {
    setComputerPlayers(players => players.map((p, i) => 
      i === index ? { ...p, ...opponentData, id: p.id } : p
    ));
  };

  const validateAndStartGame = () => {
    if (!humanPlayer.name.trim()) {
      alert("Please enter your name");
      return;
    }
    
    const invalidComputers = computerPlayers.filter(p => !p.name.trim() || !p.handicap);
    if (invalidComputers.length > 0) {
      alert("Please fill in all computer player details");
      return;
    }
    
    if (!selectedCourse) {
      alert("Please select a course");
      return;
    }
    
    onStartGame();
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
      <Card>
        <h2 style={{ color: theme.colors.primary, marginBottom: theme.spacing[5] }}>
          🎮 Wolf Goat Pig Simulation Mode
        </h2>
        <p style={{ marginBottom: 20 }}>
          Practice Wolf Goat Pig against computer opponents! This mode helps you learn the betting strategies
          and get comfortable with the game mechanics. After each hole, you'll receive educational feedback
          about your decisions.
        </p>
        
        {/* Human Player Setup */}
        <Card>
          <h3>Your Details</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Input
              label="Your Name:"
              value={humanPlayer.name}
              onChange={(e) => setHumanPlayer({...humanPlayer, name: e.target.value})}
            />
            <Input
              label="Your Handicap:"
              type="number"
              value={humanPlayer.handicap}
              onChange={(e) => setHumanPlayer({...humanPlayer, handicap: e.target.value})}
            />
          </div>
          
          <Button 
            variant="secondary"
            size="small"
            onClick={() => openGhinLookup("human")}
            style={{ marginTop: theme.spacing[2] }}
          >
            Lookup GHIN Handicap
          </Button>
          
          {ghinLookupSlot === "human" && (
            <Card variant="info" style={{ marginTop: theme.spacing[2] }}>
              <h4>GHIN Handicap Lookup</h4>
              <Input
                placeholder="First Name (optional)"
                value={ghinLookupFirstName}
                onChange={e => setGhinLookupFirstName(e.target.value)}
              />
              <Input
                placeholder="Last Name (required)"
                value={ghinLookupLastName}
                onChange={e => setGhinLookupLastName(e.target.value)}
              />
              <div style={{ display: 'flex', gap: theme.spacing[2], marginTop: theme.spacing[2] }}>
                <Button 
                  size="small"
                  onClick={doGhinLookup} 
                  disabled={ghinLookupLoading}
                >
                  Search
                </Button>
                <Button 
                  variant="error"
                  size="small"
                  onClick={closeGhinLookup}
                >
                  Cancel
                </Button>
              </div>
              
              {ghinLookupLoading && <div style={{ color: theme.colors.textSecondary, marginTop: 8 }}>Searching...</div>}
              {ghinLookupError && <div style={{ color: theme.colors.error, marginTop: 8 }}>{ghinLookupError}</div>}
              
              {ghinLookupResults.length > 0 && (
                <div style={{ marginTop: theme.spacing[2] }}>
                  <h5>Results:</h5>
                  {ghinLookupResults.map((g, idx) => (
                    <div 
                      key={idx} 
                      style={{ 
                        padding: 8, 
                        border: `1px solid ${theme.colors.border}`, 
                        borderRadius: 6, 
                        marginBottom: 4, 
                        cursor: "pointer", 
                        background: theme.colors.paper 
                      }} 
                      onClick={() => selectGhinGolfer(g)}
                    >
                      <strong>{g.name}</strong> (H: {g.handicap}) 
                      {g.club && <span style={{ color: theme.colors.textSecondary }}>@ {g.club}</span>}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}
        </Card>

        {/* Computer Players Setup */}
        <Card>
          <h3>Computer Opponents</h3>
          {computerPlayers.map((player, index) => (
            <Card key={index} variant="default" style={{ marginBottom: 16 }}>
              <h4>Computer Player {index + 1}</h4>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <Input
                  label="Name:"
                  value={player.name}
                  onChange={(e) => {
                    setComputerPlayers(players => players.map((p, i) => 
                      i === index ? { ...p, name: e.target.value } : p
                    ));
                  }}
                />
                <Input
                  label="Handicap:"
                  type="number"
                  value={player.handicap}
                  onChange={(e) => {
                    setComputerPlayers(players => players.map((p, i) => 
                      i === index ? { ...p, handicap: e.target.value } : p
                    ));
                  }}
                />
              </div>
              
              <Select
                label="Personality:"
                value={player.personality}
                onChange={(e) => {
                  setComputerPlayers(players => players.map((p, i) => 
                    i === index ? { ...p, personality: e.target.value } : p
                  ));
                }}
                options={personalities.map(p => ({ value: p.id, label: p.name }))}
                placeholder="Select personality..."
              />
              
              <Button 
                variant="secondary"
                size="small"
                onClick={() => openGhinLookup(`comp${index+1}`)}
                style={{ marginTop: theme.spacing[2] }}
              >
                Lookup GHIN Handicap
              </Button>
              
              {ghinLookupSlot === `comp${index+1}` && (
                <Card variant="info" style={{ marginTop: theme.spacing[2] }}>
                  <h4>GHIN Handicap Lookup</h4>
                  <Input
                    placeholder="First Name (optional)"
                    value={ghinLookupFirstName}
                    onChange={e => setGhinLookupFirstName(e.target.value)}
                  />
                  <Input
                    placeholder="Last Name (required)"
                    value={ghinLookupLastName}
                    onChange={e => setGhinLookupLastName(e.target.value)}
                  />
                  <div style={{ display: 'flex', gap: theme.spacing[2], marginTop: theme.spacing[2] }}>
                    <Button 
                      size="small"
                      onClick={doGhinLookup} 
                      disabled={ghinLookupLoading}
                    >
                      Search
                    </Button>
                    <Button 
                      variant="error"
                      size="small"
                      onClick={closeGhinLookup}
                    >
                      Cancel
                    </Button>
                  </div>
                  
                  {ghinLookupLoading && <div style={{ color: theme.colors.textSecondary, marginTop: 8 }}>Searching...</div>}
                  {ghinLookupError && <div style={{ color: theme.colors.error, marginTop: 8 }}>{ghinLookupError}</div>}
                  
                  {ghinLookupResults.length > 0 && (
                    <div style={{ marginTop: theme.spacing[2] }}>
                      <h5>Results:</h5>
                      {ghinLookupResults.map((g, idx) => (
                        <div 
                          key={idx} 
                          style={{ 
                            padding: 8, 
                            border: `1px solid ${theme.colors.border}`, 
                            borderRadius: 6, 
                            marginBottom: 4, 
                            cursor: "pointer", 
                            background: theme.colors.paper 
                          }} 
                          onClick={() => selectGhinGolfer(g)}
                        >
                          <strong>{g.name}</strong> (H: {g.handicap}) 
                          {g.club && <span style={{ color: theme.colors.textSecondary }}>@ {g.club}</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              )}
              
              <div style={{ marginTop: theme.spacing[2] }}>
                <span style={{ fontSize: 14, color: theme.colors.textSecondary }}>Quick select:</span>
                <div style={{ display: 'flex', gap: theme.spacing[1], marginTop: theme.spacing[1], flexWrap: 'wrap' }}>
                  {suggestedOpponents.map((opponent, oppIdx) => (
                    <Button
                      key={oppIdx}
                      variant="ghost"
                      size="small"
                      onClick={() => loadSuggestedOpponent(opponent, index)}
                    >
                      {opponent.name}
                    </Button>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </Card>

        {/* Course Selection */}
        <Card>
          <Select
            label="Select Course:"
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            options={Object.keys(courses).map(courseId => ({ 
              value: courseId, 
              label: courses[courseId]?.name || courseId 
            }))}
            placeholder="Choose a course..."
          />
        </Card>

        {/* Start Game Button */}
        <div style={{ textAlign: 'center', marginTop: theme.spacing[4] }}>
          <Button
            variant="primary"
            size="large"
            onClick={validateAndStartGame}
          >
            🚀 Start Simulation
          </Button>
        </div>
      </Card>
    </div>
  );
};

GameSetup.propTypes = {
  humanPlayer: PropTypes.object.isRequired,
  setHumanPlayer: PropTypes.func.isRequired,
  computerPlayers: PropTypes.array.isRequired,
  setComputerPlayers: PropTypes.func.isRequired,
  selectedCourse: PropTypes.string,
  setSelectedCourse: PropTypes.func.isRequired,
  courses: PropTypes.object.isRequired,
  setCourses: PropTypes.func.isRequired,
  personalities: PropTypes.array,
  setPersonalities: PropTypes.func.isRequired,
  suggestedOpponents: PropTypes.array,
  setSuggestedOpponents: PropTypes.func.isRequired,
  onStartGame: PropTypes.func.isRequired,
};

export default GameSetup;