# Wolf Goat Pig - Shot Types & Real-Time Tracking

The system distinguishes between **4 main shot types** based on distance and lie, with different physics and probabilities for each.

---

## Shot Type Categories

### 🏌️ TEE SHOTS (First shot of hole)
**Lie Type:** `"tee"`
**Distance:** Depends on par and handicap
**Characteristics:**
- Par 3: 5-65 yards to pin
- Par 4: 120-280 yards remaining
- Par 5: 180-380 yards remaining

**GameStateWidget Display:**
```
┌─────────────────────────────────────────────┐
│ 🎯 Shot Progression                          │
│ Shot #1 - TEE SHOT                           │
│ Next to Hit: Bob                             │
│                                              │
│ 👥 Player Status                             │
│ ┌─────────────────────────┐                 │
│ │ Bob 🏌️                  │                 │
│ │ TEE SHOT                 │                 │
│ │ 150 yds • Shot #1        │                 │
│ │ Lie: Tee                 │                 │
│ └─────────────────────────┘                 │
└─────────────────────────────────────────────┘
```

---

### 🎯 APPROACH SHOTS (100+ yards)
**Lie Type:** `"fairway"`, `"rough"`, `"bunker"`
**Distance:** 100-300+ yards
**Characteristics:**
- Full swing shots
- Advancement varies by lie:
  - **Fairway:** 100% distance
  - **Rough:** 80% distance
  - **Sand/Bunker:** 60% distance

**GameStateWidget Display:**
```
┌─────────────────────────────────────────────┐
│ 👥 Player Status                             │
│ ┌─────────────────────────┐                 │
│ │ Scott                    │                 │
│ │ APPROACH SHOT            │                 │
│ │ 120 yds • Shot #2        │                 │
│ │ Lie: Fairway ✅          │                 │
│ └─────────────────────────┘                 │
│                                              │
│ ┌─────────────────────────┐                 │
│ │ Vince                    │                 │
│ │ APPROACH SHOT            │                 │
│ │ 180 yds • Shot #2        │                 │
│ │ Lie: Rough ⚠️            │                 │
│ └─────────────────────────┘                 │
└─────────────────────────────────────────────┘
```

**Betting Opportunity Trigger:**
```json
{
  "type": "short_approach",
  "description": "Player has short approach shot (85 yards)",
  "strategic_value": "medium"
}
```

---

### 🏌️‍♂️ CHIPS & PITCHES (15-100 yards)
**Lie Type:** `"fairway"`, `"rough"`, `"bunker"`, `"green"`
**Distance:** 15-100 yards
**Characteristics:**

#### Pitch Shots (50-100 yards)
- Full or 3/4 swing
- Can stick it close on excellent shots (2-10 yds)
- Average: 8-25 yards remaining

#### Chip Shots (15-50 yards)
- Partial swing around green
- Excellent: 0-5 yards (might hole it!)
- Good: 2-8 yards
- Average: 4-12 yards
- Poor: 8-20 yards

**GameStateWidget Display:**
```
┌─────────────────────────────────────────────┐
│ 👥 Player Status                             │
│ ┌─────────────────────────┐                 │
│ │ Bob                      │                 │
│ │ PITCH SHOT (65 yds)      │                 │
│ │ 65 yds • Shot #3         │                 │
│ │ Lie: Fairway             │                 │
│ └─────────────────────────┘                 │
│                                              │
│ ┌─────────────────────────┐                 │
│ │ Mike                     │                 │
│ │ CHIP SHOT (25 yds)       │                 │
│ │ 25 yds • Shot #3         │                 │
│ │ Lie: Rough around green  │                 │
│ └─────────────────────────┘                 │
└─────────────────────────────────────────────┘
```

---

### ⛳ PUTTS (0-15 yards on green)
**Lie Type:** `"green"`
**Distance:** 0-15 yards
**Characteristics:**

#### Very Short Putts (0-3 yards)
- Should go in most of the time
- Excellent: 90% make rate
- Average: 60% make rate

#### Medium Putts (3-15 yards)
- Lag putting range
- Excellent: Get within 0-2 yards
- Good: 0-4 yards
- Average: 1-6 yards

**GameStateWidget Display:**
```
┌─────────────────────────────────────────────┐
│ 👥 Player Status                             │
│ ┌─────────────────────────┐                 │
│ │ Scott ⛳                 │                 │
│ │ PUTT (8 feet)            │                 │
│ │ 2.7 yds • Shot #3        │                 │
│ │ Lie: Green               │                 │
│ └─────────────────────────┘                 │
│                                              │
│ ┌─────────────────────────┐                 │
│ │ Bob ⛳                   │                 │
│ │ SHORT PUTT (4 feet)      │                 │
│ │ 1.3 yds • Shot #4        │                 │
│ │ Lie: Green - Makeable!   │                 │
│ └─────────────────────────┘                 │
└─────────────────────────────────────────────┘
```

**Betting Opportunity Trigger:**
```json
{
  "type": "putting_duel",
  "description": "All players on green - prime time for doubles",
  "strategic_value": "high"
}
```

---

## Complete Hole Example with Shot Types

### Hole 1 - Par 4, 380 yards

**Shot #1-4: Tee Shots**
```
Bob:   🏌️ TEE → 150 yds (Fairway)
Scott: 🏌️ TEE → 120 yds (Fairway) ⭐
Vince: 🏌️ TEE → 200 yds (Rough) ⚠️
Mike:  🏌️ TEE → 180 yds (Fairway)
```

**Shot #5: Approach**
```
Scott: 🎯 APPROACH (120 yds from fairway)
       Result: 5 yds to pin (Green) ⭐⭐
```

**Shot #6: Approach**
```
Bob:   🎯 APPROACH (150 yds from fairway)
       Result: 35 yds to pin (Green)
```

**Shot #7: Approach**
```
Mike:  🎯 APPROACH (180 yds from fairway)
       Result: 25 yds to pin (Fairway) - Short!
```

**Shot #8: Approach**
```
Vince: 🎯 APPROACH (200 yds from rough)
       Result: 140 yds to pin (Rough) - Still out! ⚠️
```

**Shot #9: Chip**
```
Mike:  🏌️‍♂️ CHIP (25 yds from fairway)
       Result: 8 yds to pin (Green)
```

**Shot #10: Approach**
```
Vince: 🎯 APPROACH (140 yds from rough)
       Result: 40 yds to pin (Fairway)
```

**Shot #11: Putt**
```
Scott: ⛳ PUTT (5 yds on green)
       Result: 1 yd to pin ⭐
```

**Shot #12: Putt**
```
Mike:  ⛳ PUTT (8 yds on green)
       Result: 2 yds to pin
```

**Shot #13: Chip**
```
Bob:   🏌️‍♂️ CHIP (35 yds on green)
       Result: 5 yds to pin
```

**Shot #14: Chip**
```
Vince: 🏌️‍♂️ CHIP (40 yds from fairway)
       Result: 12 yds to pin (Green)
```

**Shot #15: Short Putt**
```
Scott: ⛳ SHORT PUTT (1 yd)
       Result: HOLED! ⛳✅ (3 shots total)
```

**Shot #16: Short Putt**
```
Mike:  ⛳ SHORT PUTT (2 yds)
       Result: HOLED! ⛳✅ (4 shots total)
```

**Shot #17: Putt**
```
Bob:   ⛳ PUTT (5 yds)
       Result: HOLED! ⛳✅ (4 shots total)
```

**Shot #18: Putt**
```
Vince: ⛳ PUTT (12 yds)
       Result: 3 yds to pin
```

**Shot #19: Short Putt**
```
Vince: ⛳ SHORT PUTT (3 yds)
       Result: HOLED! ⛳✅ (5 shots total)
```

---

## How GameStateWidget Shows Shot Context

### During Approach Shots:
```
┌─────────────────────────────────────────────┐
│ 🎯 Shot Progression                          │
│ Shot #7 - APPROACH PHASE                     │
│ Next to Hit: Mike (180 yds from fairway)    │
│                                              │
│ 💰 Betting Opportunities                     │
│ ⚠️ Short approach shots available            │
│ Consider doubling before green               │
└─────────────────────────────────────────────┘
```

### During Chipping:
```
┌─────────────────────────────────────────────┐
│ 🎯 Shot Progression                          │
│ Shot #9 - SHORT GAME                         │
│ Next to Hit: Mike (25 yds chip)             │
│                                              │
│ 💰 Betting Opportunities                     │
│ 🎯 Pressure chip - key moment               │
└─────────────────────────────────────────────┘
```

### During Putting:
```
┌─────────────────────────────────────────────┐
│ 🎯 Shot Progression                          │
│ Shot #11 - PUTTING DUEL                      │
│ Next to Hit: Scott (5 yds putt)             │
│                                              │
│ 💰 Betting Opportunities                     │
│ 🔥 ALL PLAYERS ON GREEN                      │
│ Prime time for doubles!                      │
│ Strategic value: HIGH                        │
└─────────────────────────────────────────────┘
```

---

## Shot Type Logic in Code

### Determination Flow:

```javascript
if (shot_count === 1) {
  shot_type = "TEE SHOT"
  lie_type = "tee"
} else if (distance > 100) {
  shot_type = "APPROACH SHOT"
  lie_type = determine_from_previous_shot()
} else if (distance > 15) {
  if (distance > 50) {
    shot_type = "PITCH SHOT"
  } else {
    shot_type = "CHIP SHOT"
  }
  lie_type = determine_from_position()
} else if (distance <= 15 && lie_type === "green") {
  if (distance <= 3) {
    shot_type = "SHORT PUTT"
  } else {
    shot_type = "PUTT"
  }
}
```

### Lie Type Tracking:

```json
{
  "ball_positions": {
    "p1": {
      "distance_to_pin": 150,
      "lie_type": "fairway",
      "shot_count": 1
    },
    "p2": {
      "distance_to_pin": 5,
      "lie_type": "green",
      "shot_count": 2
    }
  }
}
```

---

## Betting Triggers by Shot Type

### Tee Shots Complete:
- Partnership window opens after 2+ tee shots
- Captain sees shot results before choosing

### Approach Shots (100+ yards):
- Strategic doubles when someone is in trouble
- "Short approach" trigger at <100 yards

### Short Game (15-100 yards):
- Pressure moments when chipping around green
- "One player approaching" trigger

### On the Green (Putting):
- **HIGHEST value betting moment**
- "Putting duel" - all players on green
- Final opportunity before hole completes

---

## Summary

The system tracks shot types through:

1. **Shot Count** - First shot is always a tee shot
2. **Distance to Pin** - Determines approach/chip/putt
3. **Lie Type** - Affects difficulty and shot physics
4. **Shot Quality** - Handicap-based probability

**GameStateWidget displays:**
- Clear shot type labels (TEE/APPROACH/CHIP/PUTT)
- Distance and lie information
- Strategic betting opportunities at key moments
- Visual indicators for shot quality (⭐ excellent, ⚠️ trouble)

This creates authentic golf progression with strategic betting windows based on actual shot types!
