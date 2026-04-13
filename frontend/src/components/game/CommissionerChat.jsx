import React, { useState, useRef, useEffect } from 'react';
import './CommissionerChat.css';
import { apiConfig } from '../../config/api.config';

/**
 * CommissionerChat - On-field rules expert chat component
 * @param {object} gameState - Current game state for context-aware responses
 * @param {boolean} inline - If true, renders inline instead of floating bubble
 * @param {function} onSaveToNotes - Callback when user wants to save response to notes
 * @param {boolean} startOpen - If true, chat starts in open state (for inline mode)
 */
const CommissionerChat = ({ gameState, inline = false, onSaveToNotes, startOpen = false }) => {
  const [isOpen, setIsOpen] = useState(startOpen || inline);
  const [messages, setMessages] = useState([
    {
      type: 'commissioner',
      text: "Hey there! I'm your on-field Commissioner. Need help with rules, betting, or game clarification? Just ask!",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = { type: 'user', text: inputValue, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const apiBase = apiConfig.baseUrl;
      const resp = await fetch(`${apiBase}/api/commissioner/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.text, game_state: gameState || null }),
      });
      const json = await resp.json();
      const text = json?.data?.response || json?.detail || 'Sorry, I could not get a response.';
      setMessages(prev => [...prev, { type: 'commissioner', text, timestamp: new Date() }]);
    } catch {
      setMessages(prev => [...prev, {
        type: 'commissioner',
        text: 'Connection error — check your network and try again.',
        timestamp: new Date(),
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();  // async, intentionally not awaited
    }
  };

  // Inline mode - renders directly in page flow
  if (inline) {
    return (
      <div className="commissioner-chat-inline">
        <div className="chat-window inline-chat">
          <div className="chat-header">
            <div className="chat-header-content">
              <span className="chat-icon">🏆</span>
              <div>
                <h3>Ask the Commissioner</h3>
                <p className="chat-subtitle">Rules clarification for this hole</p>
              </div>
            </div>
          </div>

          <div className="chat-messages" style={{ maxHeight: '200px' }}>
            {messages.slice(-4).map((msg, idx) => (
              <div
                key={idx}
                className={`message ${msg.type === 'user' ? 'user-message' : 'commissioner-message'}`}
              >
                {msg.type === 'commissioner' && (
                  <div className="message-avatar">🏆</div>
                )}
                <div className="message-content">
                  <div className="message-text">{msg.text}</div>
                  <div className="message-footer">
                    <div className="message-time">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    {msg.type === 'commissioner' && onSaveToNotes && idx > 0 && (
                      <button
                        className="save-to-notes-btn"
                        onClick={() => onSaveToNotes(msg.text)}
                        title="Add this ruling to hole notes"
                      >
                        📝 Save to Notes
                      </button>
                    )}
                  </div>
                </div>
                {msg.type === 'user' && (
                  <div className="message-avatar user-avatar">👤</div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="message commissioner-message">
                <div className="message-avatar">🏆</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            <input
              type="text"
              className="chat-input"
              placeholder="Ask about rules, betting, disputes..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button
              className="send-button"
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
            >
              ➤
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Floating mode - renders as floating bubble
  return (
    <div className="commissioner-chat">
      {/* Chat Bubble Button */}
      <button
        className={`chat-bubble ${isOpen ? 'hidden' : ''}`}
        onClick={() => setIsOpen(true)}
        aria-label="Open Commissioner Chat"
      >
        <span className="bubble-icon">🏆</span>
        <span className="bubble-label">Commissioner</span>
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <div className="chat-header-content">
              <span className="chat-icon">🏆</span>
              <div>
                <h3>Commissioner</h3>
                <p className="chat-subtitle">On-Field Rules Expert</p>
              </div>
            </div>
            <button
              className="close-button"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ✕
            </button>
          </div>

          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`message ${msg.type === 'user' ? 'user-message' : 'commissioner-message'}`}
              >
                {msg.type === 'commissioner' && (
                  <div className="message-avatar">🏆</div>
                )}
                <div className="message-content">
                  <div className="message-text">{msg.text}</div>
                  <div className="message-footer">
                    <div className="message-time">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    {msg.type === 'commissioner' && onSaveToNotes && idx > 0 && (
                      <button
                        className="save-to-notes-btn"
                        onClick={() => onSaveToNotes(msg.text)}
                        title="Add this ruling to hole notes"
                      >
                        📝 Save to Notes
                      </button>
                    )}
                  </div>
                </div>
                {msg.type === 'user' && (
                  <div className="message-avatar user-avatar">👤</div>
                )}
              </div>
            ))}

            {isTyping && (
              <div className="message commissioner-message">
                <div className="message-avatar">🏆</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            <input
              type="text"
              className="chat-input"
              placeholder="Ask about rules, betting, phases..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <button
              className="send-button"
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommissionerChat;
