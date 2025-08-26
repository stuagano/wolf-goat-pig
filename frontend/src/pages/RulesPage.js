import React from 'react';
import { useNavigate } from 'react-router-dom';

function RulesPage() {
  const navigate = useNavigate();
  
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '40px',
          marginBottom: '30px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
          textAlign: 'center'
        }}>
          <h1 style={{ 
            fontSize: '3rem', 
            fontWeight: 'bold',
            color: '#1F2937',
            marginBottom: '16px'
          }}>
            Wolf Goat Pig Rules
          </h1>
          <p style={{ 
            fontSize: '1.5rem', 
            color: '#6B7280'
          }}>
            Master the game, master the strategy
          </p>
        </div>

        {/* Basic Rules */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '40px',
          marginBottom: '30px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
        }}>
          <h2 style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: '#1F2937',
            marginBottom: '30px',
            display: 'flex',
            alignItems: 'center'
          }}>
            <span style={{ marginRight: '15px' }}>📖</span>
            Basic Gameplay
          </h2>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '30px'
          }}>
            <div style={{
              background: '#F3F4F6',
              padding: '25px',
              borderRadius: '12px'
            }}>
              <h3 style={{
                fontSize: '1.3rem',
                fontWeight: 'bold',
                color: '#1F2937',
                marginBottom: '15px'
              }}>
                🎯 The Setup
              </h3>
              <ul style={{
                color: '#4B5563',
                lineHeight: '1.8',
                paddingLeft: '20px'
              }}>
                <li>Played with 4 or 5 players</li>
                <li>Players rotate being the "Captain" each hole</li>
                <li>Captain tees off first and makes key decisions</li>
                <li>Each hole is a new betting opportunity</li>
              </ul>
            </div>

            <div style={{
              background: '#F3F4F6',
              padding: '25px',
              borderRadius: '12px'
            }}>
              <h3 style={{
                fontSize: '1.3rem',
                fontWeight: 'bold',
                color: '#1F2937',
                marginBottom: '15px'
              }}>
                🤝 Captain's Options
              </h3>
              <ul style={{
                color: '#4B5563',
                lineHeight: '1.8',
                paddingLeft: '20px'
              }}>
                <li><strong>Request a Partner:</strong> Team up for best-ball format</li>
                <li><strong>Go Solo:</strong> Play alone (doubles the wager)</li>
                <li>Must decide before or after tee shot</li>
                <li>Partner selection based on game format</li>
              </ul>
            </div>

            <div style={{
              background: '#F3F4F6',
              padding: '25px',
              borderRadius: '12px'
            }}>
              <h3 style={{
                fontSize: '1.3rem',
                fontWeight: 'bold',
                color: '#1F2937',
                marginBottom: '15px'
              }}>
                💰 Scoring
              </h3>
              <ul style={{
                color: '#4B5563',
                lineHeight: '1.8',
                paddingLeft: '20px'
              }}>
                <li>Winners earn "quarters" (betting units)</li>
                <li>Solo wins double the quarters</li>
                <li>Ties carry over to next hole</li>
                <li>Track quarters throughout the round</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Game Formats */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '40px',
          marginBottom: '30px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
        }}>
          <h2 style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: '#1F2937',
            marginBottom: '30px',
            display: 'flex',
            alignItems: 'center'
          }}>
            <span style={{ marginRight: '15px' }}>🐺🐐🐷</span>
            The Three Formats
          </h2>
          
          <div style={{
            display: 'grid',
            gap: '25px'
          }}>
            {/* Wolf */}
            <div style={{
              background: '#FEE2E2',
              padding: '30px',
              borderRadius: '12px',
              borderLeft: '6px solid #EF4444'
            }}>
              <h3 style={{
                fontSize: '1.5rem',
                fontWeight: 'bold',
                color: '#991B1B',
                marginBottom: '15px',
                display: 'flex',
                alignItems: 'center'
              }}>
                <span style={{ marginRight: '10px' }}>🐺</span>
                Wolf (Traditional)
              </h3>
              <p style={{
                color: '#7F1D1D',
                lineHeight: '1.8',
                marginBottom: '15px'
              }}>
                The Captain can choose their partner after seeing all tee shots. This gives 
                the Captain maximum information but also maximum pressure. The Captain must 
                decide quickly and strategically.
              </p>
              <ul style={{
                color: '#7F1D1D',
                lineHeight: '1.8',
                paddingLeft: '20px'
              }}>
                <li>Captain sees all shots before choosing</li>
                <li>Can go solo after seeing poor shots</li>
                <li>Partners split winnings equally</li>
                <li>Most strategic format</li>
              </ul>
            </div>

            {/* Goat */}
            <div style={{
              background: '#FEF3C7',
              padding: '30px',
              borderRadius: '12px',
              borderLeft: '6px solid #F59E0B'
            }}>
              <h3 style={{
                fontSize: '1.5rem',
                fontWeight: 'bold',
                color: '#78350F',
                marginBottom: '15px',
                display: 'flex',
                alignItems: 'center'
              }}>
                <span style={{ marginRight: '10px' }}>🐐</span>
                Goat (Blind)
              </h3>
              <p style={{
                color: '#451A03',
                lineHeight: '1.8',
                marginBottom: '15px'
              }}>
                The Captain must choose their partner before anyone tees off. This format 
                relies on course knowledge and player tendencies rather than actual shots. 
                It's faster but requires good judgment.
              </p>
              <ul style={{
                color: '#451A03',
                lineHeight: '1.8',
                paddingLeft: '20px'
              }}>
                <li>Partner chosen before tee shots</li>
                <li>Based on hole difficulty and player skills</li>
                <li>Faster pace of play</li>
                <li>Tests course management knowledge</li>
              </ul>
            </div>

            {/* Pig */}
            <div style={{
              background: '#F3E8FF',
              padding: '30px',
              borderRadius: '12px',
              borderLeft: '6px solid #8B5CF6'
            }}>
              <h3 style={{
                fontSize: '1.5rem',
                fontWeight: 'bold',
                color: '#581C87',
                marginBottom: '15px',
                display: 'flex',
                alignItems: 'center'
              }}>
                <span style={{ marginRight: '10px' }}>🐷</span>
                Pig (Rotating)
              </h3>
              <p style={{
                color: '#3B0764',
                lineHeight: '1.8',
                marginBottom: '15px'
              }}>
                Partners are predetermined by rotation. Each player knows who their partner 
                will be when they're Captain. This removes decision-making but adds predictability 
                and ensures everyone partners equally.
              </p>
              <ul style={{
                color: '#3B0764',
                lineHeight: '1.8',
                paddingLeft: '20px'
              }}>
                <li>Partners set by rotation order</li>
                <li>No partnership decisions needed</li>
                <li>Everyone partners with everyone</li>
                <li>Most egalitarian format</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Special Rules */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '40px',
          marginBottom: '30px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
        }}>
          <h2 style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: '#1F2937',
            marginBottom: '30px',
            display: 'flex',
            alignItems: 'center'
          }}>
            <span style={{ marginRight: '15px' }}>⚡</span>
            Special Rules & Features
          </h2>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '20px'
          }}>
            <div style={{
              background: '#DBEAFE',
              padding: '20px',
              borderRadius: '12px'
            }}>
              <h3 style={{
                fontSize: '1.2rem',
                fontWeight: 'bold',
                color: '#1E3A8A',
                marginBottom: '10px'
              }}>
                🔄 The Float
              </h3>
              <p style={{ color: '#1E40AF', lineHeight: '1.6' }}>
                When going solo, the Captain can "float" their decision until after approach 
                shots, adding another layer of strategy.
              </p>
            </div>

            <div style={{
              background: '#D1FAE5',
              padding: '20px',
              borderRadius: '12px'
            }}>
              <h3 style={{
                fontSize: '1.2rem',
                fontWeight: 'bold',
                color: '#064E3B',
                marginBottom: '10px'
              }}>
                ✨ The Option
              </h3>
              <p style={{ color: '#065F46', lineHeight: '1.6' }}>
                Players can sometimes call for "the option" to modify betting terms or 
                partnership arrangements mid-hole.
              </p>
            </div>

            <div style={{
              background: '#FED7AA',
              padding: '20px',
              borderRadius: '12px'
            }}>
              <h3 style={{
                fontSize: '1.2rem',
                fontWeight: 'bold',
                color: '#7C2D12',
                marginBottom: '10px'
              }}>
                2️⃣ Doubling
              </h3>
              <p style={{ color: '#9A3412', lineHeight: '1.6' }}>
                Certain conditions allow for doubling the bet: going solo, specific hole 
                challenges, or mutual agreement.
              </p>
            </div>

            <div style={{
              background: '#FCE7F3',
              padding: '20px',
              borderRadius: '12px'
            }}>
              <h3 style={{
                fontSize: '1.2rem',
                fontWeight: 'bold',
                color: '#831843',
                marginBottom: '10px'
              }}>
                🎭 Karl Marx
              </h3>
              <p style={{ color: '#9F1239', lineHeight: '1.6' }}>
                A special rule where all quarters are redistributed equally among players 
                under certain rare conditions.
              </p>
            </div>

            <div style={{
              background: '#F3F4F6',
              padding: '20px',
              borderRadius: '12px'
            }}>
              <h3 style={{
                fontSize: '1.2rem',
                fontWeight: 'bold',
                color: '#374151',
                marginBottom: '10px'
              }}>
                🏁 The Finish
              </h3>
              <p style={{ color: '#4B5563', lineHeight: '1.6' }}>
                Special rules apply to the final holes, including mandatory partnerships 
                or increased stakes.
              </p>
            </div>

            <div style={{
              background: '#EDE9FE',
              padding: '20px',
              borderRadius: '12px'
            }}>
              <h3 style={{
                fontSize: '1.2rem',
                fontWeight: 'bold',
                color: '#4C1D95',
                marginBottom: '10px'
              }}>
                📊 Handicaps
              </h3>
              <p style={{ color: '#5B21B6', lineHeight: '1.6' }}>
                Player handicaps are applied to level the playing field, ensuring competitive 
                matches regardless of skill level.
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div style={{
          display: 'flex',
          gap: '20px',
          justifyContent: 'center',
          marginTop: '40px'
        }}>
          <button
            onClick={() => navigate('/tutorial')}
            style={{
              padding: '14px 32px',
              background: 'white',
              color: '#3B82F6',
              border: '2px solid #3B82F6',
              borderRadius: '8px',
              fontSize: '18px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Interactive Tutorial
          </button>
          <button
            onClick={() => navigate('/')}
            style={{
              padding: '14px 32px',
              background: '#3B82F6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '18px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}

export default RulesPage;