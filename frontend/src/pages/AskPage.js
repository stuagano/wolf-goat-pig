import React, { useState, useRef, useEffect } from 'react';
import { apiConfig } from '../config/api.config';

const SUGGESTED_QUESTIONS = [
  'Who has the best all-time record?',
  'Show me the leaderboard this year',
  'Who goes solo the most?',
  "What's the biggest single-round win ever?",
  'How many rounds has each player played?',
  'Which players have the lowest handicap?',
];

const WELCOME_MESSAGE = {
  type: 'commissioner',
  text: "Welcome to the Office of Commissioner Hover Over. I have access to every round, every bet, and every statistical footnote in WGP history. Ask me anything — records, leaderboards, head-to-head matchups, trends, or obscure trivia. I'll pull the data and give you the straight story.",
  timestamp: new Date(),
  table_data: null,
  sql_used: null,
};

function isNumeric(value) {
  if (value == null || value === '') return false;
  return !isNaN(Number(value));
}

function DataTable({ tableData }) {
  if (!tableData || !tableData.columns || !tableData.rows) return null;

  const { columns, rows, row_count, truncated } = tableData;

  return (
    <div style={{ marginTop: '12px' }}>
      <div style={{
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch',
        borderRadius: '8px',
        border: '1px solid #E5E7EB',
      }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '0.82rem',
          minWidth: columns.length > 3 ? '500px' : 'auto',
        }}>
          <thead>
            <tr>
              {columns.map((col, i) => (
                <th key={i} style={{
                  padding: '8px 12px',
                  background: '#1F2937',
                  color: '#F9FAFB',
                  fontWeight: 600,
                  textAlign: 'left',
                  whiteSpace: 'nowrap',
                  borderBottom: '2px solid #374151',
                }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri} style={{
                background: ri % 2 === 0 ? '#FFFFFF' : '#F9FAFB',
              }}>
                {columns.map((col, ci) => {
                  const val = row[col] ?? row[ci] ?? '';
                  const numeric = isNumeric(val);
                  return (
                    <td key={ci} style={{
                      padding: '7px 12px',
                      borderBottom: '1px solid #E5E7EB',
                      textAlign: numeric ? 'right' : 'left',
                      whiteSpace: 'nowrap',
                    }}>
                      {String(val)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {truncated && (
        <p style={{
          fontSize: '0.75rem',
          color: '#9CA3AF',
          marginTop: '6px',
          fontStyle: 'italic',
        }}>
          (showing first {rows.length} of more results)
        </p>
      )}
    </div>
  );
}

function SqlToggle({ sql }) {
  const [visible, setVisible] = useState(false);

  if (!sql) return null;

  return (
    <div style={{ marginTop: '8px' }}>
      <button
        onClick={() => setVisible(v => !v)}
        style={{
          background: 'none',
          border: '1px solid #D1D5DB',
          borderRadius: '4px',
          padding: '3px 10px',
          fontSize: '0.72rem',
          color: '#6B7280',
          cursor: 'pointer',
          fontFamily: 'inherit',
        }}
      >
        {visible ? 'Hide SQL' : 'View SQL'}
      </button>
      {visible && (
        <pre style={{
          marginTop: '6px',
          background: '#1E1E2E',
          color: '#A6E3A1',
          padding: '12px',
          borderRadius: '6px',
          fontSize: '0.75rem',
          fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace",
          overflowX: 'auto',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          lineHeight: 1.5,
        }}>
          {sql}
        </pre>
      )}
    </div>
  );
}

function AskPage() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const showSuggestions = messages.length === 1 && messages[0] === WELCOME_MESSAGE;

  const handleSend = async (text) => {
    const question = (text || inputValue).trim();
    if (!question || isTyping) return;

    const userMsg = {
      type: 'user',
      text: question,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    try {
      const apiBase = apiConfig.baseUrl;
      const resp = await fetch(`${apiBase}/api/commissioner/data-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      const json = await resp.json();

      if (json.success && json.data) {
        setMessages(prev => [...prev, {
          type: 'commissioner',
          text: json.data.response,
          timestamp: new Date(),
          table_data: json.data.table_data || null,
          sql_used: json.data.sql_used || null,
        }]);
      } else {
        setMessages(prev => [...prev, {
          type: 'commissioner',
          text: json.detail || 'The Commissioner could not process that request. Try rephrasing your question.',
          timestamp: new Date(),
          table_data: null,
          sql_used: null,
        }]);
      }
    } catch {
      setMessages(prev => [...prev, {
        type: 'commissioner',
        text: 'Connection error — the Commissioner is temporarily unreachable. Check your network and try again.',
        timestamp: new Date(),
        table_data: null,
        sql_used: null,
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChipClick = (question) => {
    handleSend(question);
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px 20px 100px 20px',
      boxSizing: 'border-box',
    }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 140px)',
        minHeight: '400px',
      }}>
        {/* Card Container */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{
            padding: '20px 24px',
            borderBottom: '1px solid #E5E7EB',
            background: 'linear-gradient(135deg, #1F2937 0%, #374151 100%)',
            borderRadius: '16px 16px 0 0',
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
          }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem',
              flexShrink: 0,
            }}>
              <span role="img" aria-label="Commissioner">&#x2696;&#xFE0F;</span>
            </div>
            <div>
              <h1 style={{
                margin: 0,
                fontSize: '1.25rem',
                fontWeight: 700,
                color: '#F9FAFB',
                letterSpacing: '-0.01em',
              }}>
                Commissioner Hover Over
              </h1>
              <p style={{
                margin: '2px 0 0',
                fontSize: '0.82rem',
                color: '#9CA3AF',
                fontWeight: 400,
              }}>
                All-Knowing WGP Statistician &amp; Historian
              </p>
            </div>
          </div>

          {/* Messages Area */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}>
            {messages.map((msg, idx) => (
              <div key={idx} style={{
                display: 'flex',
                justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start',
                alignItems: 'flex-start',
                gap: '10px',
              }}>
                {msg.type === 'commissioner' && (
                  <div style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '50%',
                    background: '#F3F4F6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1rem',
                    flexShrink: 0,
                    marginTop: '2px',
                  }}>
                    <span role="img" aria-label="Commissioner">&#x2696;&#xFE0F;</span>
                  </div>
                )}

                <div style={{
                  maxWidth: '80%',
                  minWidth: 0,
                }}>
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: msg.type === 'user'
                      ? '16px 16px 4px 16px'
                      : '16px 16px 16px 4px',
                    background: msg.type === 'user'
                      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                      : '#FFFFFF',
                    color: msg.type === 'user' ? '#FFFFFF' : '#1F2937',
                    border: msg.type === 'user' ? 'none' : '1px solid #E5E7EB',
                    fontSize: '0.9rem',
                    lineHeight: 1.55,
                    wordBreak: 'break-word',
                    boxShadow: msg.type === 'user'
                      ? 'none'
                      : '0 1px 3px rgba(0,0,0,0.06)',
                  }}>
                    {msg.text}
                  </div>

                  {msg.type === 'commissioner' && msg.table_data && (
                    <DataTable tableData={msg.table_data} />
                  )}

                  {msg.type === 'commissioner' && msg.sql_used && (
                    <SqlToggle sql={msg.sql_used} />
                  )}

                  <div style={{
                    fontSize: '0.7rem',
                    color: '#9CA3AF',
                    marginTop: '4px',
                    textAlign: msg.type === 'user' ? 'right' : 'left',
                    paddingLeft: msg.type === 'user' ? 0 : '4px',
                    paddingRight: msg.type === 'user' ? '4px' : 0,
                  }}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isTyping && (
              <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
              }}>
                <div style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '50%',
                  background: '#F3F4F6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1rem',
                  flexShrink: 0,
                }}>
                  <span role="img" aria-label="Commissioner">&#x2696;&#xFE0F;</span>
                </div>
                <div style={{
                  padding: '12px 16px',
                  borderRadius: '16px 16px 16px 4px',
                  background: '#FFFFFF',
                  border: '1px solid #E5E7EB',
                  display: 'flex',
                  gap: '5px',
                  alignItems: 'center',
                }}>
                  {[0, 1, 2].map(i => (
                    <span key={i} style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: '#9CA3AF',
                      display: 'inline-block',
                      animation: `askPageBounce 1.4s infinite ease-in-out both`,
                      animationDelay: `${i * 0.16}s`,
                    }} />
                  ))}
                </div>
              </div>
            )}

            {/* Suggested questions */}
            {showSuggestions && !isTyping && (
              <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '8px',
                marginTop: '8px',
              }}>
                {SUGGESTED_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleChipClick(q)}
                    style={{
                      background: 'linear-gradient(135deg, rgba(102,126,234,0.08) 0%, rgba(118,75,162,0.08) 100%)',
                      border: '1px solid rgba(102,126,234,0.3)',
                      borderRadius: '20px',
                      padding: '8px 16px',
                      fontSize: '0.82rem',
                      color: '#4F46E5',
                      cursor: 'pointer',
                      fontFamily: 'inherit',
                      transition: 'all 0.15s ease',
                      lineHeight: 1.3,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102,126,234,0.15) 0%, rgba(118,75,162,0.15) 100%)';
                      e.currentTarget.style.borderColor = 'rgba(102,126,234,0.5)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'linear-gradient(135deg, rgba(102,126,234,0.08) 0%, rgba(118,75,162,0.08) 100%)';
                      e.currentTarget.style.borderColor = 'rgba(102,126,234,0.3)';
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div style={{
            padding: '16px 24px',
            borderTop: '1px solid #E5E7EB',
            background: '#FAFAFA',
            borderRadius: '0 0 16px 16px',
            display: 'flex',
            gap: '10px',
            alignItems: 'center',
          }}>
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask Commissioner Hover Over anything..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isTyping}
              style={{
                flex: 1,
                padding: '12px 16px',
                borderRadius: '24px',
                border: '1px solid #D1D5DB',
                fontSize: '0.9rem',
                fontFamily: 'inherit',
                outline: 'none',
                background: '#FFFFFF',
                color: '#1F2937',
                transition: 'border-color 0.15s ease',
              }}
              onFocus={(e) => { e.target.style.borderColor = '#667eea'; }}
              onBlur={(e) => { e.target.style.borderColor = '#D1D5DB'; }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!inputValue.trim() || isTyping}
              style={{
                width: '44px',
                height: '44px',
                borderRadius: '50%',
                border: 'none',
                background: (!inputValue.trim() || isTyping)
                  ? '#D1D5DB'
                  : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: '#FFFFFF',
                fontSize: '1.1rem',
                cursor: (!inputValue.trim() || isTyping) ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'opacity 0.15s ease',
              }}
              aria-label="Send message"
            >
              &#10148;
            </button>
          </div>
        </div>
      </div>

      {/* Keyframe animation for typing dots */}
      <style>{`
        @keyframes askPageBounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

export default AskPage;
