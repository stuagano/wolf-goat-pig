import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import '../../styles/mobile-touch.css';

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
      borderRadius: '12px',
      padding: '16px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      {/* Header - Mobile Optimized */}
      <div className="mobile-nav-header" style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '16px',
        paddingBottom: '12px',
        borderBottom: '1px solid #e5e7eb',
        flexWrap: 'wrap'
      }}>
        <button
          onClick={onBack}
          className="mobile-back-button"
          style={{
            minWidth: '48px',
            minHeight: '48px',
            padding: '12px',
            background: '#f3f4f6',
            color: '#374151',
            border: 'none',
            borderRadius: '10px',
            cursor: 'pointer',
            fontSize: '18px',
            fontWeight: '600',
            touchAction: 'manipulation',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          ←
        </button>

        <div style={{ flex: 1, minWidth: '200px' }}>
          <h2 style={{
            margin: 0,
            color: '#1f2937',
            fontSize: '18px',
            fontWeight: '700'
          }}>
            🏌️ Daily Signup
          </h2>
          {user && (
            <div style={{
              marginTop: '4px',
              fontSize: '13px',
              color: '#6b7280'
            }}>
              {user.name || user.email}
            </div>
          )}
        </div>
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

      {/* Main Date Display - Prominent */}
      <div style={{
        background: 'linear-gradient(135deg, #047857 0%, #059669 100%)',
        padding: '16px',
        borderRadius: '12px',
        marginBottom: '16px',
        textAlign: 'center',
        color: 'white'
      }}>
        <div style={{
          fontSize: '20px',
          fontWeight: '700'
        }}>
          {formatDateDisplay(selectedDate)}
        </div>
      </div>

      {/* Date Selection Bar - Horizontally Scrollable */}
      <div style={{
        background: '#f9fafb',
        padding: '12px',
        borderRadius: '12px',
        marginBottom: '16px'
      }}>
        <div style={{
          fontSize: '13px',
          color: '#6b7280',
          marginBottom: '8px',
          fontWeight: '600',
          textAlign: 'center'
        }}>
          Tap to change day
        </div>
        <div
          className="mobile-date-picker"
          style={{
            display: 'flex',
            gap: '8px',
            overflowX: 'auto',
            WebkitOverflowScrolling: 'touch',
            padding: '4px',
            scrollbarWidth: 'none',
            msOverflowStyle: 'none'
          }}
        >
          {Array.from({length: 7}, (_, i) => {
            const date = new Date(selectedDate);
            date.setDate(date.getDate() - 3 + i);
            const dateStr = date.toISOString().split('T')[0];
            const isSelected = dateStr === selectedDate;
            const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
            const dayNum = date.getDate();

            return (
              <button
                key={dateStr}
                onClick={() => {
                  if (onBack) {
                    window.location.hash = `#daily/${dateStr}`;
                    window.location.reload();
                  }
                }}
                className={`mobile-date-button ${isSelected ? 'active' : ''}`}
                style={{
                  flexShrink: 0,
                  minWidth: '60px',
                  padding: '10px 12px',
                  background: isSelected ? '#047857' : 'white',
                  color: isSelected ? 'white' : '#374151',
                  border: isSelected ? '2px solid #047857' : '2px solid #e5e7eb',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                  textAlign: 'center',
                  touchAction: 'manipulation',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ fontSize: '12px', opacity: 0.8 }}>{dayName}</div>
                <div style={{ fontSize: '18px', fontWeight: '700' }}>{dayNum}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content Grid - Responsive */}
      <div
        className="responsive-grid-3"
        style={{
          display: 'grid',
          gap: '16px'
        }}
      >
        {/* Players Who Signed Up - Most Important on Mobile */}
        <div className="mobile-card" style={{
          background: '#fff',
          borderRadius: '12px',
          overflow: 'hidden',
          border: '2px solid #047857'
        }}>
          <div style={{
            background: '#047857',
            color: 'white',
            padding: '14px 16px',
            fontWeight: '700',
            fontSize: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            ⛳ Players Signed Up
            <span style={{
              background: 'rgba(255,255,255,0.2)',
              padding: '2px 10px',
              borderRadius: '12px',
              fontSize: '14px'
            }}>
              {signupData.players.length}
            </span>
          </div>
          <div style={{ padding: '16px' }}>
            {signupData.players && signupData.players.length > 0 ? (
              <div>
                {signupData.players.map((player, index) => (
                  <div key={index} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '8px',
                    padding: '12px',
                    background: '#f9fafb',
                    borderRadius: '10px',
                    border: '1px solid #e5e7eb'
                  }}>
                    <div style={{ fontSize: '15px', fontWeight: '600', color: '#1f2937' }}>
                      {index + 1}. {player.player_name}
                    </div>
                    {player.preferred_start_time && (
                      <div style={{
                        fontSize: '13px',
                        color: '#6b7280',
                        background: '#e5e7eb',
                        padding: '4px 10px',
                        borderRadius: '6px'
                      }}>
                        {player.preferred_start_time}
                      </div>
                    )}
                  </div>
                ))}

                {isAuthenticated && !signupData.players.some(p =>
                  p.player_name === (user?.name || user?.email)
                ) && (
                  <button
                    onClick={handleSignup}
                    className="mobile-button mobile-button-primary mobile-button-full"
                    style={{
                      width: '100%',
                      minHeight: '52px',
                      padding: '14px',
                      background: '#047857',
                      color: 'white',
                      border: 'none',
                      borderRadius: '10px',
                      fontSize: '16px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      marginTop: '12px',
                      touchAction: 'manipulation'
                    }}
                  >
                    + Sign Me Up
                  </button>
                )}
              </div>
            ) : (
              <div style={{
                textAlign: 'center',
                padding: '20px'
              }}>
                <div style={{
                  color: '#6b7280',
                  fontSize: '15px',
                  marginBottom: '16px'
                }}>
                  No one signed up yet
                </div>
                {isAuthenticated && (
                  <button
                    onClick={handleSignup}
                    className="mobile-button mobile-button-primary mobile-button-full"
                    style={{
                      width: '100%',
                      minHeight: '52px',
                      padding: '14px',
                      background: '#047857',
                      color: 'white',
                      border: 'none',
                      borderRadius: '10px',
                      fontSize: '16px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      touchAction: 'manipulation'
                    }}
                  >
                    ⛳ Be the first to sign up!
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Message Board */}
        <div className="mobile-card" style={{
          background: '#fff',
          borderRadius: '12px',
          overflow: 'hidden',
          border: '2px solid #e5e7eb'
        }}>
          <div style={{
            background: '#3b82f6',
            color: 'white',
            padding: '14px 16px',
            fontWeight: '700',
            fontSize: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            💬 Messages
            <span style={{
              background: 'rgba(255,255,255,0.2)',
              padding: '2px 10px',
              borderRadius: '12px',
              fontSize: '14px'
            }}>
              {signupData.messages.length}
            </span>
          </div>
          <div style={{
            padding: '16px',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{
              flex: 1,
              overflowY: 'auto',
              maxHeight: '200px',
              marginBottom: '12px'
            }}>
              {signupData.messages && signupData.messages.length > 0 ? (
                signupData.messages.map((message, index) => (
                  <div key={message.id || index} style={{
                    marginBottom: '10px',
                    padding: '12px',
                    background: '#f9fafb',
                    borderRadius: '10px',
                    border: '1px solid #e5e7eb'
                  }}>
                    <div style={{
                      fontWeight: '600',
                      fontSize: '14px',
                      color: '#374151',
                      marginBottom: '4px'
                    }}>
                      {message.player_name}
                    </div>
                    <div style={{ fontSize: '15px', color: '#4b5563', lineHeight: '1.4' }}>
                      {message.message}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{
                  textAlign: 'center',
                  color: '#9ca3af',
                  fontSize: '14px',
                  padding: '24px'
                }}>
                  No messages yet
                </div>
              )}
            </div>

            {isAuthenticated ? (
              <div>
                <textarea
                  placeholder="Post a message..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  className="mobile-form-control"
                  style={{
                    width: '100%',
                    minHeight: '60px',
                    padding: '12px',
                    fontSize: '16px',
                    border: '2px solid #e5e7eb',
                    borderRadius: '10px',
                    resize: 'none',
                    marginBottom: '10px',
                    boxSizing: 'border-box'
                  }}
                />
                <button
                  onClick={handlePostMessage}
                  disabled={!newMessage.trim()}
                  className="mobile-button mobile-button-full"
                  style={{
                    width: '100%',
                    minHeight: '48px',
                    padding: '12px',
                    background: newMessage.trim() ? '#3b82f6' : '#9ca3af',
                    color: 'white',
                    border: 'none',
                    borderRadius: '10px',
                    fontSize: '15px',
                    fontWeight: '600',
                    cursor: newMessage.trim() ? 'pointer' : 'not-allowed',
                    touchAction: 'manipulation'
                  }}
                >
                  Post Message
                </button>
              </div>
            ) : (
              <div style={{
                textAlign: 'center',
                fontSize: '14px',
                color: '#6b7280',
                padding: '12px'
              }}>
                Login to post messages
              </div>
            )}
          </div>
        </div>

        {/* Tee Times Column */}
        <div className="mobile-card" style={{
          background: '#fff',
          borderRadius: '12px',
          overflow: 'hidden',
          border: '2px solid #e5e7eb'
        }}>
          <div style={{
            background: '#6b7280',
            color: 'white',
            padding: '14px 16px',
            fontWeight: '700',
            fontSize: '16px'
          }}>
            ⏰ Tee Times
          </div>
          <div style={{ padding: '16px' }}>
            <div style={{
              marginBottom: '10px',
              fontSize: '14px',
              color: '#6b7280'
            }}>
              Add tee times (one per line)
            </div>
            <textarea
              placeholder="e.g., 8:00 AM"
              value={teeTimesText}
              onChange={(e) => setTeeTimesText(e.target.value)}
              className="mobile-form-control"
              style={{
                width: '100%',
                minHeight: '120px',
                padding: '12px',
                fontSize: '16px',
                border: '2px solid #e5e7eb',
                borderRadius: '10px',
                resize: 'none',
                boxSizing: 'border-box'
              }}
            />
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