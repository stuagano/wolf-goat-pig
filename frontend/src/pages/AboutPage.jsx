import React from 'react';
import { useNavigate } from 'react-router-dom';

function AboutPage() {
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
            The Home of Wolf, Goat, Pig
          </h1>
          <p style={{ 
            fontSize: '1.5rem', 
            color: '#6B7280',
            fontStyle: 'italic'
          }}>
            "Where else would you rather be?"
          </p>
        </div>

        {/* Main Content Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
          gap: '30px',
          marginBottom: '30px'
        }}>
          {/* Origins Section */}
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '30px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
          }}>
            <h2 style={{
              fontSize: '1.8rem',
              fontWeight: 'bold',
              color: '#1F2937',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center'
            }}>
              <span style={{ marginRight: '10px' }}>🏌️</span>
              Origins at Wing Point
            </h2>
            <p style={{
              color: '#4B5563',
              lineHeight: '1.8',
              marginBottom: '15px'
            }}>
              Wolf Goat Pig has been a cherished tradition at Wing Point Golf & Country Club 
              since 1903. What started as a friendly wager between members has evolved into 
              the club's most beloved betting game.
            </p>
            <p style={{
              color: '#4B5563',
              lineHeight: '1.8'
            }}>
              Located on beautiful Bainbridge Island, Wing Point provides the perfect backdrop 
              for this strategic golf game where every hole brings new opportunities and challenges.
            </p>
          </div>

          {/* Game Philosophy */}
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '30px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
          }}>
            <h2 style={{
              fontSize: '1.8rem',
              fontWeight: 'bold',
              color: '#1F2937',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center'
            }}>
              <span style={{ marginRight: '10px' }}>🎯</span>
              Our Philosophy
            </h2>
            <p style={{
              lineHeight: '1.8',
              marginBottom: '15px',
              fontSize: '1.2rem',
              fontWeight: '600',
              color: '#3B82F6'
            }}>
              "We accept bad golf, but not bad betting"
            </p>
            <p style={{
              color: '#4B5563',
              lineHeight: '1.8'
            }}>
              This mantra embodies the spirit of Wolf Goat Pig. While not everyone can shoot par, 
              everyone can master the art of strategic wagering. It's about knowing when to partner, 
              when to go solo, and when to double down.
            </p>
          </div>
        </div>

        {/* Wing Point Connection */}
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
            textAlign: 'center'
          }}>
            Wing Point Golf & Country Club
          </h2>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 2fr',
            gap: '40px',
            alignItems: 'center'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'center'
            }}>
              <div style={{
                background: 'linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%)',
                padding: '30px',
                borderRadius: '16px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                color: 'white'
              }}>
                <div style={{ fontSize: '4rem', marginBottom: '10px' }}>W</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>EST. 1903</div>
              </div>
            </div>
            
            <div>
              <p style={{
                color: '#4B5563',
                lineHeight: '1.8',
                marginBottom: '20px'
              }}>
                Wing Point Golf & CC is a private club where golfers and their families have 
                enjoyed membership since 1903. Equipped with a championship golf course, social 
                and dining programs, pool, tennis, and a venue to celebrate special occasions, 
                Wing Point is truly a treasure on Bainbridge Island.
              </p>
              
              <div style={{
                background: '#F3F4F6',
                padding: '20px',
                borderRadius: '12px',
                marginTop: '20px'
              }}>
                <h3 style={{
                  fontSize: '1.2rem',
                  fontWeight: 'bold',
                  color: '#1F2937',
                  marginBottom: '15px'
                }}>
                  Club Information
                </h3>
                <div style={{ color: '#4B5563', lineHeight: '1.8' }}>
                  <p><strong>Location:</strong> 811 Cherry Avenue, Bainbridge Island, WA 98110</p>
                  <p><strong>Clubhouse Phone:</strong> 206.842.2688</p>
                  <p><strong>Golf Shop Phone:</strong> 206.842.7933</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Traditions Section */}
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
            textAlign: 'center'
          }}>
            Game Traditions & Culture
          </h2>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '20px'
          }}>
            <div style={{
              background: '#FEF3C7',
              padding: '25px',
              borderRadius: '12px',
              borderLeft: '4px solid #F59E0B'
            }}>
              <h3 style={{
                fontSize: '1.3rem',
                fontWeight: 'bold',
                color: '#92400E',
                marginBottom: '15px',
                display: 'flex',
                alignItems: 'center'
              }}>
                <span style={{ marginRight: '10px' }}>🏆</span>
                The Banquet
              </h3>
              <p style={{ color: '#78350F', lineHeight: '1.6' }}>
                Players who complete 20+ rounds qualify for the annual Wolf Goat Pig Banquet, 
                a celebration of the season's most dedicated players.
              </p>
            </div>

            <div style={{
              background: '#DBEAFE',
              padding: '25px',
              borderRadius: '12px',
              borderLeft: '4px solid #3B82F6'
            }}>
              <h3 style={{
                fontSize: '1.3rem',
                fontWeight: 'bold',
                color: '#1E3A8A',
                marginBottom: '15px',
                display: 'flex',
                alignItems: 'center'
              }}>
                <span style={{ marginRight: '10px' }}>📊</span>
                The Leaderboard
              </h3>
              <p style={{ color: '#1E40AF', lineHeight: '1.6' }}>
                Track your quarters won, games played, and overall ranking. The leaderboard 
                creates friendly competition and bragging rights throughout the season.
              </p>
            </div>

            <div style={{
              background: '#D1FAE5',
              padding: '25px',
              borderRadius: '12px',
              borderLeft: '4px solid #10B981'
            }}>
              <h3 style={{
                fontSize: '1.3rem',
                fontWeight: 'bold',
                color: '#064E3B',
                marginBottom: '15px',
                display: 'flex',
                alignItems: 'center'
              }}>
                <span style={{ marginRight: '10px' }}>🤝</span>
                The Community
              </h3>
              <p style={{ color: '#065F46', lineHeight: '1.6' }}>
                More than just a game, Wolf Goat Pig brings together golfers of all skill 
                levels to enjoy camaraderie, competition, and the beautiful Wing Point course.
              </p>
            </div>
          </div>
        </div>

        {/* Call to Action */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '40px',
          textAlign: 'center',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
        }}>
          <h2 style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: '#1F2937',
            marginBottom: '20px'
          }}>
            Ready to Join the Tradition?
          </h2>
          <p style={{
            color: '#4B5563',
            fontSize: '1.2rem',
            marginBottom: '30px'
          }}>
            Whether you're a Wing Point member or just learning about the game, 
            Wolf Goat Pig welcomes all who appreciate strategic golf betting.
          </p>
          <div style={{
            display: 'flex',
            gap: '20px',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={() => navigate('/tutorial')}
              style={{
                padding: '14px 32px',
                background: '#10B981',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '18px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Learn How to Play
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
    </div>
  );
}

export default AboutPage;
