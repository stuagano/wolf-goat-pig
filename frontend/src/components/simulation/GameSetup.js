import React, { useState, useEffect } from 'react';
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
  personalities,
  setPersonalities,
  suggestedOpponents,
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
    // Fetch courses
    fetch(`${API_URL}/courses`)
      .then(res => res.json())
      .then(data => setCourses(data))
      .catch(console.error);
    
    // Fetch personalities
    fetch(`${API_URL}/personalities`)
      .then(res => res.json())
      .then(data => setPersonalities(data))
      .catch(console.error);
    
    // Fetch suggested opponents
    fetch(`${API_URL}/suggested_opponents`)
      .then(res => res.json())
      .then(data => setSuggestedOpponents(data))
      .catch(console.error);
  }, [setCourses, setPersonalities, setSuggestedOpponents]);

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

export default GameSetup;