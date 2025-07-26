# 🐺🐐🐷 Wolf Goat Pig Golf Game Simulation

A comprehensive implementation of the "Wolf Goat Pig" golf betting game based on the complete rules from Wing Point Golf & Country Club. This simulation provides both a robust backend engine and an intuitive frontend interface for playing the game.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Game Rules Summary](#game-rules-summary)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Technical Architecture](#technical-architecture)
- [Testing](#testing)
- [Contributing](#contributing)

## 🎯 Overview

Wolf Goat Pig is a complex golf betting game that transforms ordinary golf into an intricate strategic experience. This implementation captures all the nuanced rules from the original Wing Point GCC documentation, including:

- **Player Roles**: Captain, Aardvark, Goat, and special positions
- **Team Formation**: Partnership dynamics and solo play
- **Betting Conventions**: Complex wagering with doubles, floats, and special rules
- **Game Phases**: Regular play, Vinnie's Variation, and Hoepfinger phase
- **Special Rules**: The Duncan, The Tunkarri, Karl Marx Rule, and more

## ✨ Features

### Backend (simulation.py)
- **Complete Rule Implementation**: All rules from rules.txt accurately implemented
- **Game State Management**: Comprehensive tracking of all game variables
- **Player Roles & Team Formation**: Captain, Aardvark, partnerships, solo play
- **Betting Engine**: Complex wagering calculations with all special rules
- **Phase Management**: Automatic transitions between game phases
- **AI Players**: Computer players with personality-based decision making
- **Error Handling**: Robust validation and error management

### Frontend Interface
- **Intuitive UI**: User-friendly interface for all game actions
- **Game Setup**: Configurable player count (4, 5, or 6 players)
- **Real-time State**: Live updates of scores, teams, and betting
- **Rules Reference**: Built-in rules summary and help
- **Visual Indicators**: Clear display of roles, phases, and special conditions

### Key Game Mechanics Implemented

#### Player Roles
- **Captain** 👑: First player in hitting order each hole
- **Aardvark** 🐘: 5th/6th players in 5/6-man games
- **Goat** 🐐: Player furthest down in points
- **Invisible Aardvark**: Special 4-man game mechanic

#### Team Formation
- **Partnership Requests**: Captain can request specific partners
- **Partnership Responses**: Accept/decline with automatic solo fallback
- **Aardvark Dynamics**: Request to join teams or go solo
- **Team Tossing**: Rejection mechanics with wager doubling

#### Betting Conventions
- **Base Wagering**: Quarter-based betting system
- **The Float** 🏃: Captain can double base wager (once per round)
- **The Option** ⚡: Auto-double when Captain is furthest down
- **Doubles**: Team-based doubling with acceptance/decline
- **Karl Marx Rule**: Fair point distribution based on standings

#### Special Rules
- **The Duncan** 👑: Captain solo with 3-for-2 payout
- **The Tunkarri** 🐘: Aardvark solo with 3-for-2 payout
- **Ackerley's Gambit**: Team member opt-out mechanics
- **Line of Scrimmage**: Betting restrictions based on ball position
- **Carry-Over**: Halved holes double next hole's wager

#### Game Phases
- **Regular Play**: Standard hole-by-hole progression
- **Vinnie's Variation**: Holes 13-16 in 4-man (double base bet)
- **Hoepfinger Phase**: Final holes with Goat choosing position
- **Joe's Special**: Goat sets hole values (2, 4, or 8 quarters)

## 🎮 Game Rules Summary

### Basic Game Structure
1. **Random Hitting Order**: Determined by "tossing tees" on first hole
2. **Rotation**: Order rotates each hole (2nd becomes 1st, etc.)
3. **Captain Decision**: First player chooses partner or goes solo
4. **Aardvark Actions**: 5th/6th players can join teams or go solo
5. **Scoring**: Best ball within teams, points distributed via Karl Marx Rule

### Special Phases
- **Holes 13-16 (4-man)**: Vinnie's Variation - double base wager
- **Final Holes**: Hoepfinger phase - Goat chooses hitting position
- **Joe's Special**: Hoepfinger hole values set by Goat

### Betting Rules
- **Base**: 1 quarter per hole (2 on major championship days)
- **Multipliers**: Float, Option, doubles, solo play
- **Restrictions**: Line of Scrimmage, balls in hole
- **Distribution**: Karl Marx Rule for fair point allocation

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Development Testing
```bash
# Run Wolf Goat Pig simulation tests
python3 test_wolf_goat_pig.py

# Run backend tests
cd backend && python run_simulation_tests.py
```

## 📖 Usage

### Starting a Game

1. **Access the Interface**: Navigate to `/wolf-goat-pig` in the frontend
2. **Configure Players**: Select 4, 5, or 6 players and set names/handicaps
3. **Start Game**: Initialize with hitting order and team formation

### Playing a Hole

1. **Captain Decision**: Choose partner or go solo
2. **Aardvark Actions**: Join teams or go solo (5/6-man games)
3. **Betting**: Offer/accept doubles, invoke special rules
4. **Scoring**: Enter hole scores and calculate points
5. **Advance**: Move to next hole with updated standings

### Special Actions

- **Invoke Float**: Captain doubles base wager (once per round)
- **Offer Double**: Challenge opposing team to double stakes
- **Go Solo**: Play individual ball against best ball of others
- **Toss Aardvark**: Reject aardvark request (doubles wager)

## 🔌 API Documentation

### Core Endpoints

#### Game Management
- `POST /wgp/start-game`: Initialize new game
- `GET /wgp/game-state`: Get current game state
- `POST /wgp/reset-game`: Reset/end current game

#### Player Actions
- `POST /wgp/request-partner`: Captain requests partner
- `POST /wgp/respond-partnership`: Accept/decline partnership
- `POST /wgp/captain-go-solo`: Captain goes solo
- `POST /wgp/aardvark-request-team`: Aardvark requests team
- `POST /wgp/aardvark-go-solo`: Aardvark goes solo

#### Betting Actions
- `POST /wgp/offer-double`: Offer double to opponents
- `POST /wgp/accept-double`: Accept double offer
- `POST /wgp/decline-double`: Decline double offer
- `POST /wgp/invoke-float`: Captain invokes The Float

#### Game Progression
- `POST /wgp/enter-scores`: Submit hole scores
- `POST /wgp/advance-hole`: Move to next hole

### Request/Response Format

```json
// Start Game Request
{
  "player_count": 4,
  "players": [
    {"id": "p1", "name": "Bob", "handicap": 10.5},
    {"id": "p2", "name": "Scott", "handicap": 15}
  ],
  "double_points_round": false,
  "annual_banquet": false
}

// Game State Response
{
  "current_hole": 1,
  "game_phase": "regular",
  "players": [...],
  "hole_state": {
    "hitting_order": ["p1", "p2", "p3", "p4"],
    "teams": {"type": "pending", "captain": "p1"},
    "betting": {"base_wager": 1, "current_wager": 1}
  }
}
```

## 🏗️ Technical Architecture

### Backend Components

#### Core Classes
- **`WolfGoatPigSimulation`**: Main game engine
- **`WGPPlayer`**: Player data and state
- **`TeamFormation`**: Team structure management
- **`BettingState`**: Wagering and doubles tracking
- **`HoleState`**: Complete hole information

#### Game Logic
- **Phase Management**: Automatic transitions and rule enforcement
- **Team Formation**: Partnership and solo play mechanics
- **Betting Engine**: Complex wagering calculations
- **Scoring System**: Karl Marx Rule implementation
- **AI Players**: Computer decision making

### Frontend Components

#### Main Components
- **`WolfGoatPigGame`**: Primary game interface
- **Game Setup**: Player configuration and game initialization
- **Game State Display**: Real-time game information
- **Action Interface**: Player decision making
- **Rules Reference**: Built-in help system

#### UI Features
- **Responsive Design**: Works on desktop and mobile
- **Visual Indicators**: Role badges, phase colors, team highlighting
- **Interactive Controls**: Buttons for all game actions
- **Real-time Updates**: Live state synchronization

## 🧪 Testing

### Test Coverage
- ✅ Game setup and initialization
- ✅ Partnership mechanics (request/accept/decline)
- ✅ Solo play mechanics (Pig)
- ✅ Aardvark mechanics (5/6-man games)
- ✅ Betting and doubling system
- ✅ Special rules (Float, Option, Duncan, Tunkarri)
- ✅ Scoring and Karl Marx rule
- ✅ Game phases (Vinnie's, Hoepfinger)
- ✅ Computer player AI
- ✅ Complete game flow

### Running Tests
```bash
# Comprehensive test suite
python3 test_wolf_goat_pig.py

# Backend validation
cd backend && python run_simulation_tests.py

# Frontend testing
cd frontend && npm test
```

## 🎯 Implementation Highlights

### Rules Compliance
- **100% Rule Coverage**: All rules from rules.txt implemented
- **Edge Cases**: Hanging Chad, Change of Mind, special scenarios
- **Phase Transitions**: Automatic progression through game phases
- **Betting Complexity**: Complete implementation of all wagering rules

### User Experience
- **Intuitive Interface**: Easy-to-use controls for complex game
- **Visual Clarity**: Clear indication of roles, teams, and phases
- **Rules Integration**: Built-in help and rule references
- **Error Prevention**: Validation prevents invalid actions

### Technical Excellence
- **Modular Design**: Clean separation of concerns
- **Defensive Coding**: Robust error handling and validation
- **Comprehensive Testing**: Full test coverage of all mechanics
- **API Documentation**: Clear endpoint specifications

## 🚧 Future Enhancements

### Planned Features
- **Tournament Mode**: Multi-round competitions
- **Statistics Tracking**: Historical performance analysis
- **Advanced AI**: Machine learning opponent strategies
- **Mobile App**: Native mobile interface
- **Real-time Multiplayer**: WebSocket-based live games

### Technical Improvements
- **Database Integration**: Persistent game storage
- **User Authentication**: Player accounts and profiles
- **Performance Optimization**: Enhanced scalability
- **Analytics Dashboard**: Game statistics and insights

## 📚 Rules Reference

The complete Wolf Goat Pig rules are implemented based on the official Wing Point Golf & Country Club documentation. Key rules include:

- **Basic Game (4 Players)**: Captain rotation and partnership dynamics
- **5-Man Game**: Aardvark mechanics and team formation
- **6-Man Game**: Dual aardvarks and complex team structures
- **Betting Conventions**: Quarters, doubles, and special wagers
- **Special Rules**: Duncan, Tunkarri, Karl Marx, and more
- **Game Phases**: Regular, Vinnie's Variation, Hoepfinger

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Set up development environment
3. Run test suite to verify setup
4. Make changes with test coverage
5. Submit pull request with documentation

### Code Standards
- **Defensive Coding**: Always validate inputs and handle errors
- **Test Coverage**: New features must include comprehensive tests
- **Documentation**: Update README and API docs for changes
- **Rules Compliance**: Ensure all changes align with official rules

## 📄 License

This project implements the Wolf Goat Pig game rules as documented by Wing Point Golf & Country Club. The implementation is for educational and recreational purposes.

---

**"We accept bad golf, but not bad betting"** - Wolf Goat Pig Motto

*Enjoy the most intricate golf betting game ever devised!* 🐺🐐🐷