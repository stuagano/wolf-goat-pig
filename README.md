# Wolf Goat Pig Golf Simulation

A sophisticated golf betting simulation system with interactive gameplay, real-time decision making, and comprehensive timeline tracking.

> **⚡ AI-Powered Development**: This project was built using the BMad Method (Business Methodology for Agile AI-driven Development), combining AI agents with Agile development methodologies for rapid, high-quality software development.

## 🚀 Quick Start

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
   ./dev.sh
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🤖 BMad Method Integration

This project demonstrates the power of AI-driven development using the BMad Method framework:

- **Structured Development**: Built using specialized AI agents (PM, Architect, Developer, QA)
- **Quality Documentation**: Comprehensive PRD, architecture specs, and user stories
- **Test-Driven Development**: Full test coverage with quality gates
- **Agile Workflow**: Story-based development with continuous validation

### For Developers New to BMad

If you're working on this project and want to use BMad Method:

1. **Quick Setup**: The BMad framework is already installed in `.bmad-core/`
2. **Documentation**: Review `docs/prd.md` and `docs/architecture.md` for project context
3. **User Guide**: See `.bmad-core/user-guide.md` for comprehensive BMad documentation
4. **Stories**: Active development stories are in `docs/stories/`

### Using BMad with This Project

```bash
# View available agents
ls .bmad-core/agents/

# Start development with story creation
@sm *create

# Implement a story
@dev implement story-xxx

# Review and refactor
@qa *review story-xxx
```

For detailed BMad documentation, see the [comprehensive user guide](./.bmad-core/user-guide.md).

## 📁 Project Structure

```
wolf-goat-pig/
├── .bmad-core/             # BMad Method framework
├── backend/                # FastAPI backend application
├── frontend/               # React frontend application
├── docs/                   # BMad documentation & specs
│   ├── prd.md             # Product Requirements Document
│   ├── architecture.md    # System architecture
│   └── stories/           # Development user stories
└── [deployment configs]   # Render, Vercel, etc.
```

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
./run_tests.sh
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

This project uses the BMad Method for development:

1. Fork the repository
2. Review the project documentation in `docs/`
3. Create user stories following the BMad format
4. Use BMad agents for implementation (@sm, @dev, @qa)
5. Follow the test-driven development practices
6. Submit a pull request with comprehensive tests

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the [API Documentation](http://localhost:8000/docs) when running locally
- Review the BMad documentation in `.bmad-core/user-guide.md`
- Review the test suite for usage examples
- Open an issue on GitHub

---

**Wolf Goat Pig Golf Simulation** - The most realistic golf betting experience with interactive gameplay and educational insights, built with AI-powered development using the BMad Method.