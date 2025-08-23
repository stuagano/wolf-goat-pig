# 🎰 TV Poker-Style UX Design for Wolf-Goat-Pig

## Vision
Transform Wolf-Goat-Pig into a broadcast-quality experience like televised poker, where viewers (players) always see the complete game state, probabilities, and strategic information.

## Core UI Principles

### 1. **Always-On Information Display**
Like TV poker shows percentages and chip counts, we always show:
- Current hole status
- All player positions
- Win probabilities
- Betting amounts
- Team formations
- Shot success probabilities

### 2. **No Hidden Information**
Everything relevant is visible at all times:
- No need to click to see probabilities
- No need to navigate to see scores
- No pop-ups that hide the game state
- Decisions appear as overlays, not replacements

## Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│                      TOP STATUS BAR                          │
│  Hole 7 | Par 4 | 435 yards | Base Wager: $10 | 2x Active  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┬────────────────────┬──────────────────────┐
│   PLAYER PANEL  │   COURSE VIEW      │   METRICS PANEL      │
│                 │                    │                      │
│ 👤 Stuart       │   [Visual of Hole] │  Win Probability:    │
│ Hdcp: 18        │   🚩              │  Stuart: 28%         │
│ Points: +3      │    ⛳              │  Clive: 35%          │
│ Status: Captain │   🏌️              │  Gary: 22%           │
│                 │                    │  Bernard: 15%       │
│ 💻 Clive        │   Distance: 185yd │                      │
│ Hdcp: 8         │   To Pin           │  Shot Success:       │
│ Points: -2      │                    │  Great: 15%          │
│ Status: Partner │                    │  Good: 45%           │
│                 │                    │  OK: 30%             │
│ 💻 Gary         │                    │  Poor: 10%           │
│ Hdcp: 12        │                    │                      │
│ Points: +1      │                    │  Partnership Odds:   │
│ Status: Opponent│                    │  w/Clive: +2.3 EV    │
│                 │                    │  w/Gary: +1.1 EV     │
│ 💻 Bernard      │                    │  w/Bernard: -0.5 EV  │
│ Hdcp: 15        │                    │  Solo: +3.5 EV       │
│ Points: 0       │                    │                      │
│ Status: Opponent│                    │                      │
└─────────────────┴────────────────────┴──────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    DECISION OVERLAY                          │
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║  🎯 YOUR DECISION AS CAPTAIN                          ║  │
│  ║                                                       ║  │
│  ║  [Partner with Clive]  Expected Value: +2.3          ║  │
│  ║  [Partner with Gary]   Expected Value: +1.1          ║  │
│  ║  [Partner with Bernard] Expected Value: -0.5         ║  │
│  ║  [Go Solo 2x]         Expected Value: +3.5          ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    ACTION FEED                               │
│ 🏌️ Stuart hits driver 245 yards to fairway                  │
│ 📊 Win probability update: Stuart 28% → 31%                  │
│ 🏌️ Clive hits 3-wood 220 yards to rough                     │
│ 📊 Win probability update: Clive 35% → 32%                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. **Player Panel** (Left)
- Always visible player cards
- Live point totals
- Current status (Captain/Partner/Opponent)
- Handicaps
- Visual indicators for whose turn
- Highlight active players

### 2. **Course View** (Center)
- Visual representation of current hole
- Ball positions for all players
- Distance markers
- Shot trajectory animations
- Pin position
- Hazards and features

### 3. **Metrics Panel** (Right)
- **Win Probabilities**: Real-time percentage for each player/team
- **Shot Success Rates**: Probability of outcomes for current shot
- **Partnership EVs**: Expected value for each partnership option
- **Betting Odds**: Current wager multipliers
- **Historical Performance**: Recent hole results

### 4. **Decision Overlays**
- Appear on top of game view (semi-transparent background)
- Show all options with associated probabilities/EVs
- Timer for decision (optional)
- Recommendation engine hints

### 5. **Action Feed** (Bottom)
- Rolling feed of all actions
- Probability updates after each shot
- Key events highlighted
- Betting changes noted

## Interaction Model

### Shot Progression
```javascript
// Instead of "Play Next Shot" button, have auto-play with pause
{
  autoPlay: true,
  speed: 'normal', // 'slow', 'normal', 'fast'
  pauseOnDecision: true,
  showTrajectory: true,
  animateShots: true
}
```

### Decision Points
- Decisions pause auto-play
- Full game state remains visible
- Overlay shows options with analytics
- Click to decide, then auto-play resumes

## Visual Design

### Color Coding
- **Green**: Positive EV / Good outcomes
- **Red**: Negative EV / Poor outcomes  
- **Gold**: Captain status / Special events
- **Blue**: Your player / Your team
- **Gray**: Opponents

### Animations
- Ball flight trajectories
- Probability bars that animate on changes
- Point counters that tick up/down
- Smooth transitions between holes

### Information Hierarchy
1. **Primary**: Current action needed
2. **Secondary**: Probabilities and metrics
3. **Tertiary**: Historical data and feed

## Implementation Components

### 1. MetricsDashboard Component
```jsx
<MetricsDashboard>
  <WinProbabilities players={players} />
  <ShotProbabilities currentShot={shotState} />
  <PartnershipEVs captain={captain} players={players} />
  <BettingStatus wager={currentWager} multiplier={multiplier} />
</MetricsDashboard>
```

### 2. CourseVisualizer Component
```jsx
<CourseVisualizer>
  <HoleLayout hole={currentHole} />
  <PlayerPositions players={players} />
  <ShotAnimation shot={currentShot} />
  <DistanceMarkers />
</CourseVisualizer>
```

### 3. DecisionOverlay Component
```jsx
<DecisionOverlay show={decisionNeeded}>
  <DecisionTitle type={decisionType} />
  <DecisionOptions 
    options={availableOptions}
    showEV={true}
    showProbabilities={true}
  />
  <DecisionTimer seconds={30} />
</DecisionOverlay>
```

### 4. ActionFeed Component
```jsx
<ActionFeed>
  <FeedItem 
    icon="🏌️" 
    text="Stuart hits driver 245 yards"
    impact="+3% win probability"
  />
</ActionFeed>
```

## User Experience Flow

### 1. Game Start
- Full dashboard loads with all panels
- Initial probabilities shown
- Course view shows tee positions
- Auto-play begins

### 2. Shot Sequence
- Current player highlighted
- Shot probabilities display
- Animation shows ball flight
- Probabilities update in real-time
- Feed shows result

### 3. Decision Point
- Auto-play pauses
- Decision overlay appears
- All options shown with analytics
- User clicks choice
- Auto-play resumes

### 4. Continuous Information
- Never hide the game state
- Always show all probabilities
- Keep score visible
- Maintain player positions

## Benefits of TV Poker Style

1. **Engagement**: Always something to look at
2. **Education**: Learn from probabilities
3. **Strategy**: See EVs for all decisions
4. **Immersion**: Feels like watching golf on TV
5. **Clarity**: Never confused about game state

## Technical Requirements

### Real-time Updates
- WebSocket for live updates
- Smooth animations (60fps)
- Probability calculations on backend
- State synchronization

### Performance
- Lazy load visualizations
- Cache probability calculations
- Optimize animations
- Progressive rendering

### Responsive Design
- Tablet: Side panels collapse
- Mobile: Stacked layout
- Desktop: Full three-panel view

## Next Steps

1. Build MetricsDashboard component
2. Create CourseVisualizer with D3/Canvas
3. Implement DecisionOverlay system
4. Add ActionFeed with animations
5. Wire up auto-play mechanism
6. Add probability calculations
7. Create smooth transitions

This design creates a premium, broadcast-quality experience that makes players feel like they're in a televised golf tournament with full analytics and strategic information always visible.