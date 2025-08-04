# Wolf Goat Pig Golf Simulation

A sophisticated golf betting simulation system with interactive gameplay, real-time decision making, and comprehensive timeline tracking.

## 🏌️ Features

- **Interactive Golf Simulation**: Realistic shot-by-shot gameplay with handicap-based scoring
- **Wolf Goat Pig Rules**: Complete implementation of the classic golf betting game
- **Unified Action API**: Centralized game logic with consistent REST API
- **Timeline System**: Chronological event tracking for all game actions
- **Real GHIN Integration**: Authentic golfer data and handicap lookup
- **Monte Carlo Analysis**: Statistical simulation for strategy optimization
- **Responsive Frontend**: Modern React.js interface with real-time updates

## 🚀 Quick Start

### Automated Installation (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/wolf-goat-pig.git
   cd wolf-goat-pig
   ```

2. **Run the consolidated installer**
   ```bash
   python install.py
   ```

3. **Start the servers**
   ```bash
   # Backend
   cd backend && python -m uvicorn app.main:app --reload
   
   # Frontend (in new terminal)
   cd frontend && npm start
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Installation (Legacy)

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   python -c "from app.database import init_db; init_db()"
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=sqlite:///./wolf_goat_pig.db

# Environment
ENVIRONMENT=development

# GHIN API (optional)
GHIN_API_USER=your_email@domain.com
GHIN_API_PASS=your_password
GHIN_API_STATIC_TOKEN=optional_token

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd backend
python -m pytest tests/test_unified_action_api.py -v
```

## 🚀 Deployment

### Render Deployment

1. **Fork/Clone** this repository to your GitHub account
2. **Connect to Render**:
   - Go to [render.com](https://render.com)
   - Create a new Web Service
   - Connect your GitHub repository
   - Use the `render.yaml` configuration

3. **Environment Variables** (set in Render dashboard):
   ```
   ENVIRONMENT=production
   DATABASE_URL=<your-postgresql-url>
   GHIN_API_USER=<your-ghin-email>
   GHIN_API_PASS=<your-ghin-password>
   FRONTEND_URL=https://your-frontend-url.vercel.app
   ```

### Vercel Deployment (Frontend)

1. **Deploy Frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel will automatically detect the React app

3. **Environment Variables** (set in Vercel dashboard):
   ```
   REACT_APP_API_URL=https://your-backend-url.onrender.com
   NODE_ENV=production
   ```

### Local Production Deployment

1. **Build Frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Start Production Backend**:
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

## 📁 Project Structure

```
wolf-goat-pig/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── database.py          # Database models and setup
│   │   ├── game_state.py        # Game state management
│   │   └── wolf_goat_pig_simulation.py  # Core game logic
│   ├── tests/
│   │   └── test_unified_action_api.py   # Comprehensive test suite
│   ├── requirements.txt         # Python dependencies
│   └── Procfile                # Deployment configuration
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/              # Page components
│   │   └── App.js              # Main application
│   ├── package.json            # Node.js dependencies
│   └── public/                 # Static assets
├── render.yaml                 # Render deployment config
├── vercel.json                 # Vercel deployment config
└── requirements.txt            # Root dependencies
```

## 🔧 API Endpoints

### Unified Action API

All game interactions go through the unified Action API:

```http
POST /wgp/{game_id}/action
```

**Action Types:**
- `INITIALIZE_GAME` - Start a new game
- `PLAY_SHOT` - Take a shot
- `REQUEST_PARTNERSHIP` - Request a partner
- `RESPOND_PARTNERSHIP` - Accept/decline partnership
- `DECLARE_SOLO` - Go solo
- `OFFER_DOUBLE` - Offer to double the bet
- `ACCEPT_DOUBLE` - Accept/decline double
- `ADVANCE_HOLE` - Move to next hole

### Timeline Events

The system generates chronological timeline events for all actions:
- `game_start` - Game initialization
- `hole_start` - New hole begins
- `shot` - Player takes a shot
- `partnership_request` - Partnership requested
- `partnership_response` - Partnership accepted/declined
- `partnership_decision` - Captain decides solo/partner
- `double_offer` - Double bet offered
- `double_response` - Double bet accepted/declined

## 🎮 Game Rules

### Wolf Goat Pig Basics

1. **4 Players**: Each with different handicaps
2. **Captain Rotation**: Captain changes each hole
3. **Partnership Phase**: Captain can request partner or go solo
4. **Betting**: Doubles can be offered during play
5. **Scoring**: Net scores with handicap adjustments
6. **Points**: Winners take quarters from losers

### Key Features

- **Handicap Integration**: Real GHIN handicap lookup
- **Stroke Allocation**: Proper stroke index assignment
- **Team Formation**: Dynamic partnership decisions
- **Betting System**: Real-time double opportunities
- **Educational Feedback**: Strategy insights and analysis

## 🛠️ Development

### Adding New Features

1. **Backend Changes**:
   - Add new action types to `main.py`
   - Implement game logic in `wolf_goat_pig_simulation.py`
   - Add timeline events for tracking
   - Update tests in `test_unified_action_api.py`

2. **Frontend Changes**:
   - Add new components in `frontend/src/components/`
   - Update pages in `frontend/src/pages/`
   - Test with the Action API

### Testing

```bash
# Run all tests
cd backend
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_unified_action_api.py::TestUnifiedActionAPI::test_initialize_game -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

## 📊 Performance

- **Backend**: FastAPI with async support
- **Database**: SQLAlchemy with PostgreSQL/SQLite
- **Frontend**: React with optimized builds
- **Testing**: Comprehensive test suite with 14 test scenarios
- **Deployment**: Render (backend) + Vercel (frontend)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the [API Documentation](http://localhost:8000/docs) when running locally
- Review the test suite for usage examples
- Open an issue on GitHub

---

**Wolf Goat Pig Golf Simulation** - The most realistic golf betting experience with interactive gameplay and educational insights. 