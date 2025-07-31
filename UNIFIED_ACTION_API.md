# Unified Action API Implementation

## 🎯 **Overview**

The Unified Action API is a complete redesign of the Wolf Goat Pig backend that centralizes all game logic on the server and provides a clean, consistent interface for the frontend. This implementation perfectly addresses your timeline requirements by ensuring every game action creates a chronological event that can be displayed in a running timeline.

## ✅ **COMPLETED: Backend Cleanup and Action API Integration**

### **✅ Removed Orphaned Code**
- **Deleted orphaned services**: `betting_engine.py`, `shot_simulator.py`, `probability_calculator.py`
- **Removed archive files**: `old_simulation.py`, archive README
- **Cleaned up test files**: Removed outdated test files that were no longer relevant
- **Streamlined main.py**: Removed all old endpoints, keeping only essential ones + Action API

### **✅ Centralized Game Logic**
- **Single Source of Truth**: All game rules and state transitions are handled on the server
- **Consistent Behavior**: No client-side game logic means consistent behavior across all clients
- **Easier Testing**: Server-side logic is easier to unit test and validate
- **Security**: Game rules cannot be manipulated by client-side code

### **✅ Timeline Integration Complete**
- **Every Action Creates Timeline Event**: All game actions now properly create timeline events
- **Chronological Tracking**: Events are stored with timestamps and rich details
- **Rich Context**: Each event includes player names, descriptions, and details
- **Real-time Updates**: Timeline updates immediately after each action

## 🏗️ **Architecture Benefits**

### **✅ Centralized Game Logic**
- **Single Source of Truth**: All game rules and state transitions are handled on the server
- **Consistent Behavior**: No client-side game logic means consistent behavior across all clients
- **Easier Testing**: Server-side logic is easier to unit test and validate
- **Security**: Game rules cannot be manipulated by client-side code

### **✅ Simplified Client**
- **Display Only**: Frontend only needs to display state and send actions
- **No Complex Logic**: Client doesn't need to understand game rules
- **Consistent UI**: All clients will have the same experience
- **Easier Maintenance**: Less code duplication and complexity

### **✅ Rich Context**
- **Available Actions**: Server tells client exactly what actions are legal
- **Log Messages**: Narrative context for each action
- **Timeline Events**: Structured data for chronological display
- **Complete State**: Everything needed for UI updates

## 🔄 **API Design**

### **Single Endpoint**
```
POST /wgp/{game_id}/action
```

### **Request Structure**
```json
{
  "action_type": "PLAY_SHOT",
  "payload": {
    "target_player_name": "Bob"
  }
}
```

### **Response Structure**
```json
{
  "game_state": { ... },
  "log_message": "Scott tees off. It is Bob's turn.",
  "available_actions": [
    {
      "action_type": "PLAY_SHOT",
      "prompt": "Tee off",
      "player_turn": "Bob"
    }
  ],
  "timeline_event": {
    "id": 1,
    "timestamp": "2024-01-15T10:30:00Z",
    "type": "shot",
    "description": "Scott hits a good shot from the tee",
    "player_id": "p1",
    "player_name": "Scott",
    "details": { ... }
  }
}
```

## 🎮 **Action Types**

### **Core Game Actions**
1. **`INITIALIZE_GAME`** - Start a new game with players
2. **`PLAY_SHOT`** - Simulate a shot for the current player
3. **`REQUEST_PARTNERSHIP`** - Captain requests a specific partner
4. **`RESPOND_PARTNERSHIP`** - Accept/decline partnership request
5. **`DECLARE_SOLO`** - Captain decides to play alone
6. **`OFFER_DOUBLE`** - Offer to double the wager
7. **`ACCEPT_DOUBLE`** - Accept/decline double offer
8. **`CONCEDE_PUTT`** - Concede a putt to a player

### **Timeline Event Types**
- **`game_start`** - When a game begins
- **`hole_start`** - When a hole begins
- **`shot`** - When a player takes a shot
- **`partnership_request`** - When captain requests a partner
- **`partnership_response`** - When partner accepts/declines
- **`partnership_decision`** - When captain goes solo
- **`double_offer`** - When a double is offered
- **`double_response`** - When double is accepted/declined
- **`concession`** - When a putt is conceded

## 📊 **Data Models**

### **TimelineEvent**
```python
@dataclass
class TimelineEvent:
    id: int
    timestamp: datetime
    type: str
    description: str
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
```

### **ActionRequest**
```python
class ActionRequest(BaseModel):
    action_type: str
    payload: Optional[Dict[str, Any]] = None
```

### **ActionResponse**
```python
class ActionResponse(BaseModel):
    game_state: Dict[str, Any]
    log_message: str
    available_actions: List[Dict[str, Any]]
    timeline_event: Optional[Dict[str, Any]] = None
```

## 🎯 **Timeline Flow Example**

Here's exactly how your timeline requirement is implemented:

### **1. Initialize Game**
```json
{
  "action_type": "INITIALIZE_GAME",
  "payload": {
    "players": [
      {"name": "Scott", "handicap": 10.5},
      {"name": "Bob", "handicap": 15.0},
      {"name": "Tim", "handicap": 8.0},
      {"name": "Steve", "handicap": 20.5}
    ],
    "course_name": "Wing Point"
  }
}
```
**Response:**
```json
{
  "log_message": "Game initialized with 4 players on Wing Point",
  "timeline_event": {
    "type": "game_start",
    "description": "Game started with 4 players on Wing Point",
    "details": {"players": [...], "course": "Wing Point"}
  }
}
```

### **2. Scott Tees Off**
```json
{
  "action_type": "PLAY_SHOT",
  "payload": null
}
```
**Response:**
```json
{
  "log_message": "Scott tees off. It is Bob's turn.",
  "timeline_event": {
    "type": "shot",
    "description": "Scott hits a good shot from the tee - 245 yards to pin",
    "player_name": "Scott"
  }
}
```

### **3. Bob Tees Off**
```json
{
  "action_type": "PLAY_SHOT",
  "payload": null
}
```
**Response:**
```json
{
  "log_message": "Bob tees off. Scott must decide on partnerships.",
  "available_actions": [
    {"action_type": "DECLARE_SOLO", "prompt": "Go solo"},
    {"action_type": "REQUEST_PARTNERSHIP", "prompt": "Request partner"}
  ]
}
```

### **4. Scott Requests Bob as Partner**
```json
{
  "action_type": "REQUEST_PARTNERSHIP",
  "payload": {"target_player_name": "Bob"}
}
```
**Response:**
```json
{
  "log_message": "Scott asks Bob to be his partner.",
  "timeline_event": {
    "type": "partnership_request",
    "description": "Scott requests Bob as partner",
    "player_name": "Scott"
  }
}
```

### **5. Bob Accepts Partnership**
```json
{
  "action_type": "RESPOND_PARTNERSHIP",
  "payload": {"accepted": true}
}
```
**Response:**
```json
{
  "log_message": "Bob accepts! Teams are formed.",
  "timeline_event": {
    "type": "partnership_response",
    "description": "Bob accepts the partnership",
    "player_name": "Bob"
  }
}
```

### **6. Tim Offers Double**
```json
{
  "action_type": "OFFER_DOUBLE",
  "payload": null
}
```
**Response:**
```json
{
  "log_message": "Tim offers a double! Wager increases from 1 to 2 quarters.",
  "timeline_event": {
    "type": "double_offer",
    "description": "Tim offers a double - wager increases from 1 to 2 quarters",
    "player_name": "Tim"
  }
}
```

## 🚀 **Frontend Implementation**

The `UnifiedActionDemo.js` and `WolfGoatPigGame.js` components demonstrate how simple the frontend becomes:

### **Key Features**
- **Single Action Function**: `sendAction(actionType, payload)`
- **Automatic State Updates**: Game state updates after each action
- **Timeline Display**: Events are automatically added to timeline
- **Available Actions**: UI shows only legal next actions
- **Rich Context**: Log messages provide narrative flow

### **State Management**
```javascript
const [gameState, setGameState] = useState(null);
const [availableActions, setAvailableActions] = useState([]);
const [logMessages, setLogMessages] = useState([]);
const [timelineEvents, setTimelineEvents] = useState([]);
```

### **Action Flow**
1. User clicks action button
2. Frontend sends action to `/wgp/{game_id}/action`
3. Server processes action and updates game state
4. Server returns new state, log message, available actions, and timeline event
5. Frontend updates all state and displays new information

## 🎯 **Perfect for Your Timeline Requirements**

This implementation provides exactly what you described:

### **✅ Chronological Events**
- Every action creates a timeline event
- Events are stored with timestamps and rich details
- Frontend can display events in chronological order

### **✅ Rich Context**
- Each event includes player names, descriptions, and details
- Events are categorized by type (shot, partnership, betting)
- Visual indicators (icons, colors) for different event types

### **✅ Real-time Updates**
- Timeline updates immediately after each action
- No need to poll or refresh
- Smooth, responsive user experience

### **✅ Educational Value**
- Log messages explain what happened and why
- Timeline shows the complete story of each hole
- Users can learn from the chronological flow

## 🔧 **Implementation Status**

### **✅ Backend Complete**
- Unified action endpoint implemented
- Timeline event tracking added
- All action handlers implemented
- Rich response structure
- Orphaned code removed
- All logic centralized in backend

### **✅ Frontend Complete**
- `UnifiedActionDemo.js` component created
- `WolfGoatPigGame.js` using Action API
- Timeline display with icons and colors
- Action buttons with context
- Log message display

### **✅ Integration Complete**
- Added to main App.js routing
- Accessible via `/unified-demo` and `/wolf-goat-pig` routes
- Ready for testing and demonstration

## 🎯 **Backend Endpoints (Cleaned Up)**

### **Essential Endpoints (Kept)**
- `GET /health` - Health check
- `GET /rules` - Get Wolf Goat Pig rules
- `GET /courses` - Get available courses
- `POST /courses` - Add new course1

- `PUT /courses/{name}` - Update course
- `DELETE /courses/{name}` - Delete course
- `POST /courses/import/*` - Course import endpoints
- `GET /ghin/lookup` - GHIN golfer lookup
- `GET /ghin/diagnostic` - GHIN API diagnostic

### **Main Game Endpoint (Action API)**
- `POST /wgp/{game_id}/action` - **Unified Action API** (All game logic goes through this)

### **Removed (Orphaned)**
- All old simulation endpoints
- Old game state endpoints
- Duplicate functionality
- Unused services and utilities

## 🏆 **Benefits Achieved**

- **Perfect Timeline Support**: Every action creates a timeline event
- **Simplified Frontend**: Client only displays state and sends actions
- **Centralized Logic**: All game rules on the server
- **Rich Context**: Detailed information for UI and learning
- **Educational Value**: Clear narrative flow for users
- **Maintainable Code**: Clean separation of concerns
- **No Orphaned Code**: Removed all unused files and endpoints

## 🚀 **Next Steps**

1. **Test the Implementation**: Visit `/unified-demo` or `/wolf-goat-pig` to see the unified API in action
2. **Enhance Timeline Display**: Add more visual features to the timeline
3. **Add More Actions**: Implement additional game actions as needed
4. **Performance Optimization**: Optimize for high-traffic scenarios

This unified action API provides the perfect foundation for your Wolf Goat Pig timeline requirements while creating a much more maintainable and scalable architecture! All backend logic is now properly centralized and the timeline functionality is fully integrated. 