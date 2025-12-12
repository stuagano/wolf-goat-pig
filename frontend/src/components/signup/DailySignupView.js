import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || "";

const DailySignupView = ({ selectedDate, onBack }) => {
  const { user, isAuthenticated } = useAuth0();
  const [signupData, setSignupData] = useState({
    players: [],
    messages: [],
    tee_times: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newMessage, setNewMessage] = useState('');
  const [teeTimesText, setTeeTimesText] = useState('');
  const [teams, setTeams] = useState([]);
  const [teamFormationLoading, setTeamFormationLoading] = useState(false);
  const [showTeamFormation, setShowTeamFormation] = useState(false);
  const [generatedPairings, setGeneratedPairings] = useState(null);
  const [pairingsLoading, setPairingsLoading] = useState(false);

  // Format date for display
  const formatDateDisplay = (dateStr) => {
    const date = new Date(dateStr);
    const options = { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    };
    return date.toLocaleDateString('en-US', options);
  };

  // Load daily signup data
  const loadDailyData = async () => {
    try {
      setLoading(true);
      // Try to fetch from the weekly endpoint for this specific date
      const response = await fetch(`${API_URL}/signups/weekly-with-messages?week_start=${selectedDate}`);
      
      if (response.ok) {
        const weekData = await response.json();
        // Find the specific day's data
        const dayData = weekData.daily_summaries?.find(day => day.date === selectedDate);
        
        if (dayData) {
          setSignupData({
            players: dayData.signups || [],
            messages: dayData.messages || [],
            tee_times: []
          });
        } else {
          setSignupData({ players: [], messages: [], tee_times: [] });
        }
      } else {
        // Fallback to empty data
        setSignupData({ players: [], messages: [], tee_times: [] });
      }
      
      setError(null);
    } catch (err) {
      console.error('Error loading daily data:', err);
      setError('Unable to load signup data');
      setSignupData({ players: [], messages: [], tee_times: [] });
    } finally {
      setLoading(false);
    }
  };

  // Load generated pairings for the date
  const loadGeneratedPairings = async () => {
    try {
      setPairingsLoading(true);
      const response = await fetch(`${API_URL}/pairings/${selectedDate}`);

      if (response.ok) {
        const data = await response.json();
        if (data.exists) {
          setGeneratedPairings(data);
        } else {
          setGeneratedPairings(null);
        }
      } else {
        setGeneratedPairings(null);
      }
    } catch (err) {
      console.error('Error loading pairings:', err);
      setGeneratedPairings(null);
    } finally {
      setPairingsLoading(false);
    }
  };

  // Initialize component
  useEffect(() => {
    if (selectedDate) {
      loadDailyData();
      loadGeneratedPairings();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate]); // loadDailyData is stable, only re-run when date changes

  // Handle signing up current user
  const handleSignup = async () => {
    if (!isAuthenticated || !user) {
      setError('Please log in to sign up');
      return;
    }

    try {
      const playerName = user.name || user.email;
      
      const signupData = {
        date: selectedDate,
        player_profile_id: 1,
        player_name: playerName,
        preferred_start_time: null,
        notes: null
      };

      const response = await fetch(`${API_URL}/signups`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(signupData)
      });

      if (response.ok) {
        // Reload the data
        loadDailyData();
        setError(null);
      } else {
        throw new Error('Failed to sign up');
      }
    } catch (err) {
      console.error('Signup error:', err);
      setError('Failed to sign up. Please try again.');
    }
  };

  // Handle posting a message
  const handlePostMessage = async () => {
    if (!isAuthenticated || !user || !newMessage.trim()) {
      return;
    }

    try {
      const playerName = user.name || user.email;
      
      const messageData = {
        date: selectedDate,
        message: newMessage.trim(),
        player_profile_id: 1,
        player_name: playerName
      };

      const response = await fetch(`${API_URL}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(messageData)
      });

      if (response.ok) {
        setNewMessage('');
        loadDailyData();
        setError(null);
      } else {
        throw new Error('Failed to post message');
      }
    } catch (err) {
      console.error('Message error:', err);
      setError('Failed to post message');
    }
  };

  // Handle generating random teams
  const handleGenerateRandomTeams = async () => {
    if (signupData.players.length < 4) {
      setError('Need at least 4 players to generate teams');
      return;
    }

    try {
      setTeamFormationLoading(true);
      const response = await fetch(`${API_URL}/signups/${selectedDate}/team-formation/random`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const result = await response.json();
        setTeams(result.teams);
        setShowTeamFormation(true);
        setError(null);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate teams');
      }
    } catch (err) {
      console.error('Team formation error:', err);
      setError(`Failed to generate teams: ${err.message}`);
    } finally {
      setTeamFormationLoading(false);
    }
  };

  // Handle generating balanced teams
  const handleGenerateBalancedTeams = async () => {
    if (signupData.players.length < 4) {
      setError('Need at least 4 players to generate teams');
      return;
    }

    try {
      setTeamFormationLoading(true);
      const response = await fetch(`${API_URL}/signups/${selectedDate}/team-formation/balanced`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const result = await response.json();
        setTeams(result.teams);
        setShowTeamFormation(true);
        setError(null);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate balanced teams');
      }
    } catch (err) {
      console.error('Balanced team formation error:', err);
      setError(`Failed to generate balanced teams: ${err.message}`);
    } finally {
      setTeamFormationLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '300px',
        fontSize: '18px' 
      }}>
        Loading daily signup...
      </div>
    );
  }

  return (
    <div style={{ 
      maxWidth: '1200px', 
      margin: '0 auto',
      background: 'white',
      borderRadius: '8px',
      padding: '20px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '30px',
        borderBottom: '2px solid #dee2e6',
        paddingBottom: '15px'
      }}>
        <div>
          <h2 style={{ 
            margin: 0, 
            color: '#333',
            fontSize: '24px',
            fontWeight: 'bold'
          }}>
            🏌️ Golf Sign-up & Daily Messages
          </h2>
          <p style={{ 
            margin: '5px 0 0 0',
            color: '#6c757d',
            fontSize: '14px'
          }}>
            Manage your daily golf sign-ups, post messages, and set preferences
          </p>
          {user && (
            <div style={{
              marginTop: '8px',
              padding: '4px 8px',
              background: '#e3f2fd',
              color: '#1976d2',
              borderRadius: '4px',
              fontSize: '12px',
              display: 'inline-block'
            }}>
              Welcome, {user.name || user.email}
            </div>
          )}
        </div>
        
        <button
          onClick={onBack}
          style={{
            padding: '8px 16px',
            background: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          ← Back to Week View
        </button>
      </div>

      {error && (
        <div style={{ 
          backgroundColor: '#f8d7da', 
          color: '#721c24', 
          padding: '12px', 
          borderRadius: '4px', 
          marginBottom: '20px',
          border: '1px solid #f5c6cb'
        }}>
          {error}
        </div>
      )}

      {/* Date Selection Bar */}
      <div style={{
        background: '#f8f9fa',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        <h3 style={{ 
          margin: '0 0 10px 0',
          color: '#495057',
          fontSize: '18px'
        }}>
          Click a day
        </h3>
        <div style={{
          display: 'flex',
          gap: '10px',
          justifyContent: 'center',
          flexWrap: 'wrap'
        }}>
          {/* Generate week dates around selected date */}
          {Array.from({length: 8}, (_, i) => {
            const date = new Date(selectedDate);
            date.setDate(date.getDate() - 3 + i);
            const dateStr = date.toISOString().split('T')[0];
            const isSelected = dateStr === selectedDate;
            
            return (
              <button
                key={dateStr}
                onClick={() => {
                  // Update selected date - parent component should handle this
                  if (onBack) {
                    // For now, just show the date change visually
                    window.location.hash = `#daily/${dateStr}`;
                    window.location.reload();
                  }
                }}
                style={{
                  padding: '8px 12px',
                  background: isSelected ? '#dc3545' : '#fff',
                  color: isSelected ? 'white' : '#333',
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  minWidth: '120px'
                }}
              >
                {date.toLocaleDateString('en-US', { 
                  weekday: 'short', 
                  month: 'short', 
                  day: 'numeric' 
                })}
              </button>
            );
          })}
        </div>
      </div>

      {/* Current Standings */}
      <div style={{
        background: '#fff3cd',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        <div style={{ 
          color: '#856404', 
          fontWeight: 'bold',
          marginBottom: '10px',
          fontSize: '16px'
        }}>
          Current Standings
        </div>
        <button style={{
          background: '#ffc107',
          color: '#000',
          border: 'none',
          padding: '10px 20px',
          borderRadius: '6px',
          fontWeight: 'bold',
          cursor: 'pointer',
          fontSize: '14px'
        }}>
          New Player? Click here to sign up.
        </button>
      </div>

      {/* Main Date Display */}
      <div style={{
        background: '#fff9c4',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        <div style={{
          background: '#fff59d',
          display: 'inline-block',
          padding: '10px 25px',
          borderRadius: '6px',
          fontSize: '18px',
          fontWeight: 'bold',
          color: '#333'
        }}>
          {formatDateDisplay(selectedDate)}
        </div>
      </div>

      {/* Main Content Grid - Three Equal Columns */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gap: '20px',
        border: '2px solid #dee2e6',
        borderRadius: '8px',
        overflow: 'hidden'
      }}>
        {/* Tee Times Column */}
        <div style={{
          background: '#fff',
          borderRight: '1px solid #dee2e6'
        }}>
          <div style={{
            background: '#dc3545',
            color: 'white',
            padding: '12px',
            textAlign: 'center',
            fontWeight: 'bold',
            fontSize: '16px'
          }}>
            Tee Times
          </div>
          <div style={{
            padding: '15px'
          }}>
            <div style={{ marginBottom: '10px', fontSize: '14px', color: '#495057' }}>
              Add Tee Times
            </div>
            <textarea
              placeholder="Enter tee times, one per line (e.g. 8:00 AM)"
              value={teeTimesText}
              onChange={(e) => setTeeTimesText(e.target.value)}
              style={{
                width: '100%',
                height: '200px',
                padding: '8px',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                resize: 'none',
                fontSize: '14px'
              }}
            />
          </div>
        </div>

        {/* Players Who Signed Up Column */}
        <div style={{ 
          background: '#fff',
          borderRight: '1px solid #dee2e6'
        }}>
          <div style={{
            background: '#495057',
            color: 'white',
            padding: '12px',
            textAlign: 'center',
            fontWeight: 'bold',
            fontSize: '16px'
          }}>
            Players Signed Up ({signupData.players.length})
          </div>
          <div style={{ padding: '15px' }}>
            {signupData.players && signupData.players.length > 0 ? (
              <div>
                {signupData.players.map((player, index) => (
                  <div key={index} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '8px',
                    padding: '8px',
                    background: '#f8f9fa',
                    borderRadius: '4px',
                    border: '1px solid #dee2e6'
                  }}>
                    <div style={{ fontSize: '14px', fontWeight: '500' }}>
                      {index + 1}. {player.player_name}
                    </div>
                    {player.preferred_start_time && (
                      <div style={{ 
                        fontSize: '12px', 
                        color: '#6c757d',
                        background: '#e9ecef',
                        padding: '2px 6px',
                        borderRadius: '3px'
                      }}>
                        {player.preferred_start_time}
                      </div>
                    )}
                  </div>
                ))}
                
                {/* Add yourself button */}
                {isAuthenticated && !signupData.players.some(p => 
                  p.player_name === (user?.name || user?.email)
                ) && (
                  <button
                    onClick={handleSignup}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      background: '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '14px',
                      cursor: 'pointer',
                      marginTop: '10px'
                    }}
                  >
                    + Add Yourself
                  </button>
                )}
              </div>
            ) : (
              <div style={{
                textAlign: 'center',
                color: '#6c757d',
                fontSize: '14px',
                fontStyle: 'italic',
                padding: '20px'
              }}>
                No one signed up yet
                {isAuthenticated && (
                  <button
                    onClick={handleSignup}
                    style={{
                      display: 'block',
                      width: '100%',
                      padding: '8px 12px',
                      background: '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '14px',
                      cursor: 'pointer',
                      marginTop: '15px'
                    }}
                  >
                    Be the first to sign up!
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Message Board Column */}
        <div>
          <div style={{
            background: '#28a745',
            color: 'white',
            padding: '12px',
            textAlign: 'center',
            fontWeight: 'bold',
            fontSize: '16px'
          }}>
            Message Board ({signupData.messages.length})
          </div>
          <div style={{ 
            padding: '15px',
            height: '280px',
            display: 'flex',
            flexDirection: 'column'
          }}>
            {/* Messages Display */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              marginBottom: '15px',
              maxHeight: '180px'
            }}>
              {signupData.messages && signupData.messages.length > 0 ? (
                signupData.messages.map((message, index) => (
                  <div key={message.id || index} style={{
                    marginBottom: '10px',
                    padding: '8px',
                    background: '#f8f9fa',
                    borderRadius: '4px',
                    border: '1px solid #dee2e6'
                  }}>
                    <div style={{
                      fontWeight: 'bold',
                      fontSize: '12px',
                      color: '#495057',
                      marginBottom: '4px'
                    }}>
                      {message.player_name}
                    </div>
                    <div style={{ fontSize: '14px', color: '#333' }}>
                      {message.message}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{
                  textAlign: 'center',
                  color: '#6c757d',
                  fontSize: '14px',
                  fontStyle: 'italic',
                  padding: '20px'
                }}>
                  No messages yet
                </div>
              )}
            </div>

            {/* Message Input */}
            {isAuthenticated ? (
              <div>
                <textarea
                  placeholder="Post a message..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  style={{
                    width: '100%',
                    height: '60px',
                    padding: '8px',
                    border: '1px solid #dee2e6',
                    borderRadius: '4px',
                    resize: 'none',
                    fontSize: '14px',
                    marginBottom: '8px'
                  }}
                />
                <button
                  onClick={handlePostMessage}
                  disabled={!newMessage.trim()}
                  style={{
                    width: '100%',
                    padding: '6px 12px',
                    background: newMessage.trim() ? '#007bff' : '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '12px',
                    cursor: newMessage.trim() ? 'pointer' : 'not-allowed'
                  }}
                >
                  Post Message
                </button>
              </div>
            ) : (
              <div style={{
                textAlign: 'center',
                fontSize: '12px',
                color: '#6c757d',
                fontStyle: 'italic'
              }}>
                Login to post messages
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Official Generated Pairings Section */}
      {generatedPairings && generatedPairings.pairings && (
        <div style={{
          background: '#fff',
          borderRadius: '8px',
          marginTop: '20px',
          border: '3px solid #28a745',
          overflow: 'hidden'
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
            color: 'white',
            padding: '15px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '5px' }}>
              🎲 Official Pairings
            </div>
            <div style={{ fontSize: '14px', opacity: 0.9 }}>
              Generated {new Date(generatedPairings.generated_at).toLocaleString()}
              {generatedPairings.notification_sent && ' • Email notifications sent'}
            </div>
          </div>

          <div style={{ padding: '20px' }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '15px'
            }}>
              {generatedPairings.pairings.teams?.map((team, teamIndex) => (
                <div key={team.team_id || teamIndex} style={{
                  background: '#f8f9fa',
                  borderRadius: '8px',
                  padding: '15px',
                  border: '2px solid #28a745',
                  boxShadow: '0 2px 8px rgba(40, 167, 69, 0.15)'
                }}>
                  <div style={{
                    background: '#28a745',
                    color: 'white',
                    padding: '10px',
                    borderRadius: '6px',
                    textAlign: 'center',
                    fontWeight: 'bold',
                    fontSize: '16px',
                    marginBottom: '12px'
                  }}>
                    Group {teamIndex + 1}
                  </div>

                  {team.players?.map((player, playerIndex) => (
                    <div key={playerIndex} style={{
                      padding: '8px 12px',
                      background: '#fff',
                      marginBottom: '6px',
                      borderRadius: '4px',
                      fontSize: '15px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      border: '1px solid #dee2e6'
                    }}>
                      <span style={{ fontWeight: '500' }}>{player.player_name}</span>
                      {player.handicap && (
                        <span style={{
                          fontSize: '12px',
                          color: '#6c757d',
                          background: '#e9ecef',
                          padding: '2px 8px',
                          borderRadius: '10px'
                        }}>
                          {player.handicap} HCP
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>

            {/* Remaining players (alternates) */}
            {generatedPairings.pairings.remaining_players?.length > 0 && (
              <div style={{
                marginTop: '20px',
                padding: '15px',
                background: '#fff3cd',
                borderRadius: '8px',
                border: '1px solid #ffc107'
              }}>
                <div style={{ fontWeight: 'bold', color: '#856404', marginBottom: '10px' }}>
                  Alternates ({generatedPairings.pairings.remaining_players.length})
                </div>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  {generatedPairings.pairings.remaining_players.map((player, idx) => (
                    <span key={idx} style={{
                      background: '#ffc107',
                      color: '#333',
                      padding: '4px 12px',
                      borderRadius: '15px',
                      fontSize: '14px'
                    }}>
                      {player.player_name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div style={{
              marginTop: '15px',
              padding: '12px',
              background: '#d4edda',
              borderRadius: '6px',
              textAlign: 'center',
              fontSize: '14px',
              color: '#155724'
            }}>
              <strong>These are the official pairings.</strong> Check your email for your group assignment!
            </div>
          </div>
        </div>
      )}

      {/* Loading state for pairings */}
      {pairingsLoading && (
        <div style={{
          marginTop: '20px',
          padding: '20px',
          textAlign: 'center',
          color: '#6c757d'
        }}>
          Loading pairings...
        </div>
      )}

      {/* Team Formation Section (for ad-hoc team generation when no official pairings exist) */}
      {signupData.players.length >= 4 && !generatedPairings && (
        <div style={{
          background: '#fff',
          borderRadius: '8px',
          marginTop: '20px',
          border: '2px solid #dee2e6',
          overflow: 'hidden'
        }}>
          <div style={{
            background: '#007bff',
            color: 'white',
            padding: '15px',
            textAlign: 'center',
            fontWeight: 'bold',
            fontSize: '18px'
          }}>
            ⚡ Team Formation Available ({signupData.players.length} players)
          </div>
          
          <div style={{ padding: '20px' }}>
            <div style={{
              marginBottom: '15px',
              textAlign: 'center',
              color: '#495057'
            }}>
              With {signupData.players.length} players signed up, you can form {Math.floor(signupData.players.length / 4)} complete team(s) of 4 players each.
              {signupData.players.length % 4 > 0 && (
                <span style={{ color: '#856404' }}>
                  {' '}({signupData.players.length % 4} player{signupData.players.length % 4 > 1 ? 's' : ''} will be alternates)
                </span>
              )}
            </div>
            
            <div style={{
              display: 'flex',
              gap: '15px',
              justifyContent: 'center',
              marginBottom: '20px',
              flexWrap: 'wrap'
            }}>
              <button
                onClick={handleGenerateRandomTeams}
                disabled={teamFormationLoading}
                style={{
                  padding: '10px 20px',
                  background: teamFormationLoading ? '#6c757d' : '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: teamFormationLoading ? 'not-allowed' : 'pointer',
                  minWidth: '150px'
                }}
              >
                {teamFormationLoading ? 'Generating...' : '🎲 Random Teams'}
              </button>
              
              <button
                onClick={handleGenerateBalancedTeams}
                disabled={teamFormationLoading}
                style={{
                  padding: '10px 20px',
                  background: teamFormationLoading ? '#6c757d' : '#ffc107',
                  color: teamFormationLoading ? 'white' : '#000',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: teamFormationLoading ? 'not-allowed' : 'pointer',
                  minWidth: '150px'
                }}
              >
                {teamFormationLoading ? 'Generating...' : '⚖️ Balanced Teams'}
              </button>
              
              {showTeamFormation && teams.length > 0 && (
                <button
                  onClick={() => setShowTeamFormation(false)}
                  style={{
                    padding: '10px 20px',
                    background: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    minWidth: '150px'
                  }}
                >
                  ❌ Hide Teams
                </button>
              )}
            </div>
            
            {showTeamFormation && teams.length > 0 && (
              <div style={{
                background: '#f8f9fa',
                borderRadius: '6px',
                padding: '15px',
                border: '1px solid #dee2e6'
              }}>
                <h4 style={{
                  margin: '0 0 15px 0',
                  color: '#495057',
                  textAlign: 'center'
                }}>
                  Generated Teams ({teams.length} team{teams.length > 1 ? 's' : ''})
                </h4>
                
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                  gap: '15px'
                }}>
                  {teams.map((team, teamIndex) => (
                    <div key={team.team_id || teamIndex} style={{
                      background: '#fff',
                      borderRadius: '6px',
                      padding: '15px',
                      border: '2px solid #007bff',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                    }}>
                      <div style={{
                        background: '#007bff',
                        color: 'white',
                        padding: '8px',
                        borderRadius: '4px',
                        textAlign: 'center',
                        fontWeight: 'bold',
                        marginBottom: '10px'
                      }}>
                        Team {team.team_id || teamIndex + 1}
                        {team.average_handicap && (
                          <span style={{ fontSize: '12px', opacity: 0.9 }}>
                            {' '}(Avg. Handicap: {team.average_handicap})
                          </span>
                        )}
                      </div>
                      
                      {team.players.map((player, playerIndex) => (
                        <div key={playerIndex} style={{
                          padding: '6px 10px',
                          background: '#f8f9fa',
                          marginBottom: '5px',
                          borderRadius: '4px',
                          fontSize: '14px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}>
                          <span>{player.player_name}</span>
                          {player.handicap && (
                            <span style={{
                              fontSize: '12px',
                              color: '#6c757d',
                              background: '#e9ecef',
                              padding: '2px 6px',
                              borderRadius: '3px'
                            }}>
                              HCP: {player.handicap}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
                
                <div style={{
                  marginTop: '15px',
                  padding: '10px',
                  background: '#d1ecf1',
                  borderRadius: '4px',
                  textAlign: 'center',
                  fontSize: '14px',
                  color: '#0c5460'
                }}>
                  💡 <strong>Tip:</strong> Teams are automatically balanced based on skill level when using "Balanced Teams". 
                  Use "Random Teams" for completely random pairings.
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Not Authenticated Message */}
      {!isAuthenticated && (
        <div style={{
          background: '#f8d7da',
          color: '#721c24',
          padding: '15px',
          borderRadius: '8px',
          marginTop: '20px',
          textAlign: 'center'
        }}>
          Please log in to sign up for golf or post messages.
        </div>
      )}
    </div>
  );
};

export default DailySignupView;