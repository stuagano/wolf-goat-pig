import React, { useState, useRef, useEffect } from 'react';
import './CommissionerChat.css';

const CommissionerChat = ({ gameState }) => {
  const [isOpen, setIsOpen] = useState(false);
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
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const getCommissionerResponse = (userMessage) => {
    const msg = userMessage.toLowerCase();

    // Rule-based responses
    if (msg.includes('vinnie') || msg.includes('variation')) {
      return "Vinnie's Variation applies to 4-player games only on holes 13-16. The base wager doubles during this phase. Once you hit the Hoepfinger (hole 17), Vinnie's is over.";
    }

    if (msg.includes('hoepfinger')) {
      return `The Hoepfinger starts when everyone's had their full turns as Captain. In 4-player: hole 17. In 5-player: hole 16. In 6-player: hole 13. The Goat (furthest down) picks their tee position and can invoke Joe's Special to set the base wager at 2, 4, or 8 quarters.`;
    }

    if (msg.includes('captain')) {
      return "The Captain is the player hitting first on a given hole. They can request a partner from eligible players (those who haven't had the next player hit yet). If declined, the bet doubles and the declining player goes solo.";
    }

    if (msg.includes('aardvark')) {
      return "In 5-6 player games, the Aardvark is the 5th (or 6th) player in rotation. They can ask to join a team after teams form. If 'tossed' (rejected), they join the other team and the bet doubles. Ping-ponging the Aardvark doubles it again!";
    }

    if (msg.includes('double') || msg.includes('doubling')) {
      return "A double offers to increase the stakes on a hole. Accept it to keep playing at 2x the wager. Decline and you forfeit at the current level. Once accepted, you can redouble! But watch out for the Line of Scrimmage rule - no doubling from ahead of the furthest ball.";
    }

    if (msg.includes('karl marx') || msg.includes('odd quarter')) {
      return "Karl Marx Rule: 'From each according to his ability, to each according to his need.' When quarters can't divide evenly, the player furthest down pays/wins less. The player higher up covers the odd quarter. If tied, wait until scores diverge (Hanging Chad).";
    }

    if (msg.includes('float')) {
      return "In 4-man and 5-man games, each Captain gets one Float per round. Use it on your Captain turn to double the base wager before anyone hits. Strategic timing is key!";
    }

    if (msg.includes('option')) {
      return "The Option: If the Captain is the Goat (furthest down), the bet automatically doubles before tee shots UNLESS they turn it off. This gives the struggling player a chance to catch up with higher stakes.";
    }

    if (msg.includes('pig') || msg.includes('solo') || msg.includes('on my own')) {
      return "Going solo (being 'the Pig') means playing your ball against everyone else's best ball. The bet doubles. Invoke The Duncan by declaring before you hit to win 3 quarters for every 2 wagered!";
    }

    if (msg.includes('handicap') || msg.includes('creecher') || msg.includes('stroke')) {
      return "Creecher Feature: Your easiest 6 handicap holes are played at HALF stroke. Other holes get full strokes. Net handicaps are calculated by subtracting the lowest player's handicap from everyone's.";
    }

    if (msg.includes('carry') || msg.includes('carryover') || msg.includes('halved')) {
      return "Carry-Over: If a hole is tied (halved) by all teams, the wager on the NEXT hole doubles. But carryovers can't happen on consecutive holes - there's a limit!";
    }

    if (msg.includes('big dick')) {
      return "The Big Dick (named for Dick Duncan): On the 18th tee, the player with the most winnings can go solo against everyone else, risking ALL their winnings. The group must unanimously accept. Others can still play regular WGP amongst themselves.";
    }

    if (msg.includes('good but not in')) {
      return "'Good but not in' means we're conceding your shot for pace of play, BUT betting is still open. The ball isn't officially in the cup for betting purposes, so doubles and other wagers can continue!";
    }

    if (msg.includes('line of scrimmage')) {
      return "Line of Scrimmage: You can't offer a double if you've passed the ball furthest from the hole. This prevents power-cart riders from gaining unfair info. The LOS moves as each ball is played.";
    }

    if (msg.includes('duncan')) {
      return "The Duncan: Declare you're going solo BEFORE you hit as Captain. If you win the hole, you get paid 3 quarters for every 2 quarters wagered (3-for-2 payout). High risk, high reward!";
    }

    if (msg.includes('joe') || msg.includes('special')) {
      return "Joe's Special: At the start of the Hoepfinger, the Goat sets the hole's starting value: 2, 4, or 8 quarters (or higher if there's a natural carryover). If the Goat doesn't invoke it, the hole starts at 2Q or the carryover amount. No doubling until all tee shots are hit!";
    }

    // Game state awareness
    if (msg.includes('score') || msg.includes('winning') || msg.includes('down')) {
      const playerCount = gameState?.players?.length || 0;
      return `You have ${playerCount} players in this game. Check the scoreboard to see who's the Goat (furthest down) and who's leading. Remember, good betting can overcome bad golf!`;
    }

    if (msg.includes('hole') && gameState?.current_hole) {
      const hole = gameState.current_hole;
      const players = gameState.players?.length || 4;
      let phase = 'Regular play';

      if (players === 4 && hole >= 13 && hole <= 16) {
        phase = "Vinnie's Variation (2x base wager)";
      } else if (players === 4 && hole >= 17) {
        phase = 'Hoepfinger';
      } else if (players === 5 && hole >= 16) {
        phase = 'Hoepfinger';
      } else if (players === 6 && hole >= 13) {
        phase = 'Hoepfinger';
      }

      return `You're on hole ${hole}. Phase: ${phase}. ${phase === 'Hoepfinger' ? "The Goat picks tee position and can invoke Joe's Special!" : ''}`;
    }

    // General help
    if (msg.includes('help') || msg.includes('rules') || msg.includes('how')) {
      return "I can help with: Vinnie's Variation, Hoepfinger, Captain rules, Aardvark rules, Doubling, Karl Marx Rule, The Float, The Option, Going Solo/Pig, The Duncan, Joe's Special, Carry-Over, Line of Scrimmage, Handicaps/Creecher Feature, and more. What do you need clarification on?";
    }

    // Default responses
    const defaults = [
      "Hmm, I'm not sure about that one. Try asking about specific rules like 'Vinnie's Variation', 'Hoepfinger', 'Captain', 'Aardvark', or 'Doubling'.",
      "That's a good question! For now, try asking about: betting rules, handicaps, game phases, or specific WGP terms.",
      "I specialize in Wolf Goat Pig rules! Ask me about Vinnie's, the Hoepfinger, Karl Marx Rule, or any betting conventions."
    ];

    return defaults[Math.floor(Math.random() * defaults.length)];
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage = {
      type: 'user',
      text: inputValue,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    // Simulate typing delay
    setIsTyping(true);
    setTimeout(() => {
      const response = getCommissionerResponse(inputValue);
      const commissionerMessage = {
        type: 'commissioner',
        text: response,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, commissionerMessage]);
      setIsTyping(false);
    }, 800 + Math.random() * 700); // 800-1500ms delay for realism
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

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
                  <div className="message-time">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
