import React, { useState, useEffect } from 'react';
import { useTheme } from '../../theme/Provider';
import { Button, Card, Input, Select } from '../ui';

const API_URL = process.env.REACT_APP_API_URL || "";

interface Player {
  id?: string;
  name: string;
  handicap: string;
  personality?: string;
  is_human: boolean;
}

interface Course {
  name: string;
  holes: Array<{
    hole_number: number;
    par: number;
    yards: number;
    stroke_index: number;
    description: string;
  }>;
  total_par: number;
  total_yards: number;
  hole_count: number;
}

interface Personality {
  id: string;
  name: string;
}

interface SuggestedOpponent {
  name: string;
  handicap: string;
  personality: string;
}

interface GhinGolfer {
  name: string;
  handicap: string;
  club?: string;
}

interface GameSetupProps {
  humanPlayer: Player;
  setHumanPlayer: React.Dispatch<React.SetStateAction<Player>>;
  computerPlayers: Player[];
  setComputerPlayers: React.Dispatch<React.SetStateAction<Player[]>>;
  selectedCourse: string | null;
  setSelectedCourse: React.Dispatch<React.SetStateAction<string | null>>;
  courses: { [key: string]: Course };
  setCourses: React.Dispatch<React.SetStateAction<{ [key: string]: Course }>>;
  personalities?: Personality[];
  setPersonalities: React.Dispatch<React.SetStateAction<Personality[]>>;
  suggestedOpponents?: SuggestedOpponent[];
  setSuggestedOpponents: React.Dispatch<React.SetStateAction<SuggestedOpponent[]>>;
  onStartGame: () => void;
}

const GameSetup: React.FC<GameSetupProps> = ({
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
  const [ghinLookupSlot, setGhinLookupSlot] = useState<string | null>(null);
  const [ghinLookupFirstName, setGhinLookupFirstName] = useState("");
  const [ghinLookupLastName, setGhinLookupLastName] = useState("");
  const [ghinLookupResults, setGhinLookupResults] = useState<GhinGolfer[]>([]);
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
      .then((data: { [key: string]: Course }) => {
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
        const fallbackCourses: { [key: string]: Course } = {
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
      .then((data: Personality[]) => {
        if (Array.isArray(data)) {
          setPersonalities(data);
        } else {
          throw new Error('Invalid personalities data format');
        }
      })
      .catch(error => {
        console.error('Failed to load personalities:', error);
        // Provide fallback personalities
        const fallbackPersonalities: Personality[] = [
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
      .then((data: SuggestedOpponent[]) => {
        if (Array.isArray(data)) {
          setSuggestedOpponents(data);
        } else {
          throw new Error('Invalid suggested opponents data format');
        }
      })
      .catch(error => {
        console.error('Failed to load suggested opponents:', error);
        // Provide fallback suggested opponents
        const fallbackOpponents: SuggestedOpponent[] = [
          { name: 'Bob', handicap: '12', personality: 'aggressive' },
          { name: 'Alice', handicap: '8', personality: 'conservative' },
          { name: 'Charlie', handicap: '16', personality: 'balanced' }
        ];
        setSuggestedOpponents(fallbackOpponents);
      });
  }, [setCourses, setPersonalities, setSuggestedOpponents, selectedCourse, setSelectedCourse]);

  // Initialize computer players with suggested opponents if available
  useEffect(() => {
    if (computerPlayers.length === 0 && suggestedOpponents.length >= 3) {
      setComputerPlayers([
        { id: "comp1", ...suggestedOpponents[0], is_human: false },
        { id: "comp2", ...suggestedOpponents[1], is_human: false },
        { id: "comp3", ...suggestedOpponents[2], is_human: false }
      ]);
    } else if (computerPlayers.length === 0) {
      setComputerPlayers([
        { id: "comp1", name: "", handicap: "", personality: "", is_human: false },
        { id: "comp2", name: "", handicap: "", personality: "", is_human: false },
        { id: "comp3", name: "", handicap: "", personality: "", is_human: false }
      ]);
    }
  }, [computerPlayers, setComputerPlayers, suggestedOpponents]);

  const openGhinLookup = (slot: string) => {
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
      const data: GhinGolfer[] = await res.json();
      setGhinLookupResults(data);
      if (data.length === 0) setGhinLookupError("No golfers found");
    } catch (err) {
      setGhinLookupError("Lookup failed");
    } finally {
      setGhinLookupLoading(false);
    }
  };

  const selectGhinGolfer = (golfer: GhinGolfer) => {
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

  const loadSuggestedOpponent = (opponentData: SuggestedOpponent, index: number) => {
    setComputerPlayers(players => players.map((p, i) =>
      i === index ? { ...p, ...opponentData, id: p.id } : p
    ));
  };

  const loadAllSuggestedOpponents = () => {
    if (suggestedOpponents.length >= 3) {
      setComputerPlayers([
        { id: "comp1", ...suggestedOpponents[0], is_human: false },
        { id: "comp2", ...suggestedOpponents[1], is_human: false },
        { id: "comp3", ...suggestedOpponents[2], is_human: false }
      ]);
    }
  };

  const validateAndStartGame = () => {
    if (!humanPlayer.name.trim()) {
      alert("Please enter your name to start playing.");
      return;
    }

    const invalidComputers = computerPlayers.filter(p => !p.name.trim() || !p.handicap);
    if (invalidComputers.length > 0) {
      alert("Wolf Goat Pig requires 4 players. Please click the 'Quick Start - Use Defaults' button to automatically set up computer opponents, or fill in their details manually.");
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
        <h2 style={{ color: theme.colors.primary, marginBottom: theme.spacing }}>
          🎮 Wolf Goat Pig Simulation Mode
        </h2>
        <p style={{ marginBottom: 20 }}>
          Practice Wolf Goat Pig against computer opponents! This mode helps you learn the betting strategies
          and get comfortable with the game mechanics. After each hole, you'll receive educational feedback
          about your decisions.
        </p>

        <Card variant="info" style={{ marginBottom: 20 }}>
          <p style={{ margin: 0, fontSize: 14 }}>
            <strong>Note:</strong> Wolf Goat Pig requires 4 players to play. Don't worry - the computer opponents
            are already set up for you! Just enter your name and click "Quick Start" or customize the opponents below.
          </p>
        </Card>
        
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
            style={{ marginTop: theme.spacing }}
          >
            Lookup GHIN Handicap
          </Button>
          
          {ghinLookupSlot === "human" && (
            <Card variant="info" style={{ marginTop: theme.spacing }}>
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
              <div style={{ display: 'flex', gap: theme.spacing, marginTop: theme.spacing }}>
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
                <div style={{ marginTop: theme.spacing }}>
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: theme.spacing }}>
            <h3 style={{ margin: 0 }}>Computer Opponents</h3>
            <Button
              variant="primary"
              size="small"
              onClick={loadAllSuggestedOpponents}
            >
              🎲 Quick Start - Use Defaults
            </Button>
          </div>
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
                style={{ marginTop: theme.spacing }}
              >
                Lookup GHIN Handicap
              </Button>
              
              {ghinLookupSlot === `comp${index+1}` && (
                <Card variant="info" style={{ marginTop: theme.spacing }}>
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
                  <div style={{ display: 'flex', gap: theme.spacing, marginTop: theme.spacing }}>
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
                    <div style={{ marginTop: theme.spacing }}>
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
              
              <div style={{ marginTop: theme.spacing }}>
                <span style={{ fontSize: 14, color: theme.colors.textSecondary }}>Quick select:</span>
                <div style={{ display: 'flex', gap: theme.spacing, marginTop: theme.spacing, flexWrap: 'wrap' }}>
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
            value={selectedCourse || ''}
            onChange={(e) => setSelectedCourse(e.target.value)}
            options={Object.keys(courses).map(courseId => ({ 
              value: courseId, 
              label: courses[courseId]?.name || courseId 
            }))}
            placeholder="Choose a course..."
          />
        </Card>

        {/* Start Game Button */}
        <div style={{ textAlign: 'center', marginTop: theme.spacing }}>
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
