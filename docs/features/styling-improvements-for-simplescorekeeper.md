# LiveScorekeeper Styling Improvements for SimpleScorekeeper

## Overview
This document catalogs the specific CSS/styling patterns from the new LiveScorekeeper components that can enhance SimpleScorekeeper's visual design.

---

## 1. Color Schemes & Backgrounds

### Card/Panel Backgrounds
```css
backgroundColor: theme.colors.paper
borderRadius: theme.borderRadius.md  /* 8px */
border: 1px solid theme.colors.border
```

### Team Status Colors with Transparency
```css
/* Captain (Gold) */
borderLeft: 4px solid theme.colors.gold
backgroundColor: rgba(180, 83, 9, 0.15)  /* Dark mode */
backgroundColor: rgba(180, 83, 9, 0.08)  /* Light mode */
boxShadow: 0 2px 8px rgba(180, 83, 9, 0.12)

/* Team 1 (Primary Green) */
borderLeft: 4px solid theme.colors.primary
backgroundColor: rgba(4, 120, 87, 0.15)  /* Dark mode */
backgroundColor: rgba(4, 120, 87, 0.05)  /* Light mode */

/* Team 2/Opponents (Accent Blue) */
borderLeft: 4px solid theme.colors.accent
backgroundColor: rgba(3, 105, 161, 0.15)  /* Dark mode */
backgroundColor: rgba(3, 105, 161, 0.05)  /* Light mode */
```

### Button Backgrounds with Transparency
```css
/* Win Button (Green) */
borderColor: theme.colors.primary
backgroundColor: rgba(16, 185, 129, 0.1)  /* Dark mode */
backgroundColor: rgba(16, 185, 129, 0.05)  /* Light mode */

/* Lose Button (Red) */
borderColor: theme.colors.error
backgroundColor: rgba(220, 38, 38, 0.1)  /* Dark mode */
backgroundColor: rgba(220, 38, 38, 0.05)  /* Light mode */

/* Glass Effect Buttons */
backgroundColor: rgba(255, 255, 255, 0.2)
backgroundColor: rgba(255, 255, 255, 0.15)
```

---

## 2. Card/Panel Styling

### Enhanced Card Style
```css
backgroundColor: theme.colors.paper
borderRadius: theme.borderRadius.md  /* 8px */
border: 1px solid theme.colors.border
padding: theme.spacing[3]  /* 12px */
marginBottom: theme.spacing[2]  /* 8px */
transition: all 0.2s ease
```

### Header Card (HoleHeader)
```css
backgroundColor: theme.colors.primary
color: #ffffff
padding: theme.spacing[4]  /* 16px */
borderRadius: theme.borderRadius.md  /* 8px */
marginBottom: theme.spacing[4]  /* 16px */
```

### Box Shadow for Emphasis
```css
boxShadow: 0 2px 8px rgba(180, 83, 9, 0.12)  /* Gold captain cards */
boxShadow: theme.shadows.lg  /* Navigation bar */
```

---

## 3. Button Styles

### Primary Action Button
```css
padding: 6px theme.spacing[3]  /* 6px 12px */
fontSize: theme.typography.xs
fontWeight: theme.typography.semibold
border: none
borderRadius: 6px
cursor: pointer
transition: all 0.2s ease
```

### Navigation Buttons
```css
width: 48px
height: 48px
backgroundColor: theme.colors.gray100
border: 1px solid theme.colors.border
borderRadius: theme.borderRadius.md  /* 8px */
cursor: pointer
fontSize: theme.typography.lg
transition: all 0.15s ease
```

### Glass Effect Buttons (in HoleHeader)
```css
backgroundColor: rgba(255, 255, 255, 0.2)
border: none
color: #ffffff
padding: theme.spacing[2] theme.spacing[4]  /* 8px 16px */
borderRadius: theme.borderRadius.base  /* 6px */
cursor: pointer
fontSize: theme.typography.sm
fontWeight: theme.typography.semibold
transition: all 0.2s ease
```

### Disabled State
```css
opacity: 0.4
cursor: not-allowed
```

### Quick Preset Buttons
```css
flex: 1
padding: theme.spacing[3] theme.spacing[2]  /* 12px 8px */
backgroundColor: theme.colors.paper
border: 1px solid theme.colors.border
borderRadius: theme.borderRadius.base  /* 6px */
cursor: pointer
transition: all 0.15s ease
```

---

## 4. Typography

### Section Headers
```css
fontSize: theme.typography.xs
fontWeight: theme.typography.semibold
textTransform: uppercase
letterSpacing: 0.5px
color: theme.colors.textSecondary
marginBottom: theme.spacing[2]  /* 8px */
paddingLeft: 4px
```

### Large Numbers (Hole Number, Par)
```css
/* Hole Number */
fontSize: theme.typography['4xl']
fontWeight: theme.typography.bold
lineHeight: 1

/* Par Value */
fontSize: theme.typography['3xl']
fontWeight: theme.typography.bold
lineHeight: 1
```

### Player Names
```css
fontWeight: theme.typography.semibold
fontSize: theme.typography.base
color: theme.colors.textPrimary
```

### Input Labels
```css
fontSize: theme.typography.xs
color: theme.colors.textSecondary
marginBottom: 4px
textTransform: uppercase
letterSpacing: 0.5px
```

### Badge Text
```css
fontSize: theme.typography.xs
fontWeight: theme.typography.semibold
backgroundColor: theme.colors.gold
padding: 2px theme.spacing[2]  /* 2px 8px */
borderRadius: 10px
```

---

## 5. Spacing Patterns

### Container Padding
```css
padding: theme.spacing[4]  /* 16px */
maxWidth: 480px
margin: 0 auto
```

### Element Spacing
```css
marginBottom: theme.spacing[4]  /* 16px - sections */
marginBottom: theme.spacing[3]  /* 12px - subsections */
marginBottom: theme.spacing[2]  /* 8px - items */
gap: theme.spacing[3]  /* 12px - flex items */
gap: theme.spacing[2]  /* 8px - smaller items */
```

### Internal Padding
```css
padding: theme.spacing[3]  /* 12px - cards */
padding: theme.spacing[2] theme.spacing[3]  /* 8px 12px - inputs */
```

---

## 6. Borders & Border Radius

### Border Radius Values
```css
borderRadius: theme.borderRadius.md  /* 8px - cards, headers */
borderRadius: theme.borderRadius.base  /* 6px - buttons, inputs */
borderRadius: theme.borderRadius.full  /* 9999px - badges, pills */
borderRadius: 2px  /* progress bars */
borderRadius: 6px  /* action buttons */
borderRadius: 10px  /* small badges */
borderRadius: 12px  /* wager badges */
```

### Accent Borders
```css
borderLeft: 4px solid theme.colors.gold  /* Captain */
borderLeft: 4px solid theme.colors.primary  /* Team 1 */
borderLeft: 4px solid theme.colors.accent  /* Team 2 */
border: 1px solid theme.colors.border  /* Standard */
borderTop: 1px solid rgba(255, 255, 255, 0.2)  /* Dividers on dark bg */
```

---

## 7. Animations & Transitions

### Standard Transitions
```css
transition: all 0.2s ease  /* Cards, buttons */
transition: all 0.15s ease  /* Quick interactions */
transition: width 0.3s ease  /* Progress bars */
```

### Transform Effects
```css
/* Current hole indicator */
transform: scale(1.2)
```

---

## 8. Input Styling

### Score Input Fields
```css
width: 100%
padding: theme.spacing[2] theme.spacing[3]  /* 8px 12px */
fontSize: theme.typography.lg
fontWeight: theme.typography.semibold
textAlign: center
border: 1px solid theme.colors.border
borderRadius: theme.borderRadius.base  /* 6px */
backgroundColor: theme.colors.inputBackground
color: theme.colors.textPrimary
```

---

## 9. Progress Indicators

### Progress Bar Container
```css
marginTop: theme.spacing[3]  /* 12px */
height: 4px
backgroundColor: rgba(255, 255, 255, 0.2)
borderRadius: 2px
overflow: hidden
```

### Progress Bar Fill
```css
height: 100%
backgroundColor: #ffffff
borderRadius: 2px
transition: width 0.3s ease
width: [calculated]%
```

### Progress Dots
```css
width: 8px
height: 8px
borderRadius: 50%
backgroundColor: theme.colors.gray300  /* Default */
backgroundColor: theme.colors.primary  /* Completed */
backgroundColor: theme.colors.gold  /* Current */
transform: scale(1.2)  /* Current */
transition: all 0.15s ease
```

---

## 10. Badge Styling

### Wager Badge (Large)
```css
backgroundColor: rgba(255, 255, 255, 0.2)
padding: theme.spacing[1] theme.spacing[3]  /* 4px 12px */
borderRadius: theme.borderRadius.full  /* 9999px */
fontSize: theme.typography.sm
fontWeight: theme.typography.semibold
```

### Handicap Badge
```css
fontSize: theme.typography.sm
color: theme.colors.textSecondary
backgroundColor: theme.colors.gray200
padding: 2px theme.spacing[2]  /* 2px 8px */
borderRadius: theme.borderRadius.full  /* 9999px */
```

### Status Badge (Hoepfinger, etc.)
```css
fontSize: theme.typography.xs
backgroundColor: theme.colors.gold
padding: 2px theme.spacing[2]  /* 2px 8px */
borderRadius: 10px
fontWeight: theme.typography.semibold
```

---

## 11. Standings Display

### Standings Item
```css
display: flex
alignItems: center
gap: 4px
fontSize: theme.typography.xs
color: theme.colors.textSecondary
```

### Quarters Coloring
```css
/* Positive Quarters */
color: theme.colors.primary
fontWeight: theme.typography.semibold

/* Negative Quarters */
color: theme.colors.error
fontWeight: theme.typography.semibold
```

---

## 12. Fixed Navigation Bar

### Bottom Navigation
```css
position: fixed
bottom: 0
left: 0
right: 0
backgroundColor: theme.colors.paper
borderTop: 1px solid theme.colors.border
padding: theme.spacing[3] theme.spacing[4]  /* 12px 16px */
display: flex
justifyContent: space-between
alignItems: center
zIndex: 100
boxShadow: theme.shadows.lg
```

---

## 13. Edit Mode Indicator

### Edit Mode Header
```css
backgroundColor: theme.colors.gold
color: #ffffff
padding: theme.spacing[3] theme.spacing[4]  /* 12px 16px */
borderRadius: theme.borderRadius.base  /* 6px */
marginBottom: theme.spacing[4]  /* 16px */
display: flex
justifyContent: space-between
alignItems: center
```

### Edit Mode Buttons
```css
/* Save Button */
padding: 6px theme.spacing[3]  /* 6px 12px */
fontSize: theme.typography.xs
fontWeight: theme.typography.semibold
border: none
borderRadius: 6px
cursor: pointer
backgroundColor: #ffffff
color: theme.colors.gold

/* Cancel Button */
backgroundColor: rgba(255, 255, 255, 0.2)
color: #ffffff
```

---

## 14. Rotation Player Display

### Rotation Player Pill
```css
display: flex
alignItems: center
gap: 6px
padding: theme.spacing[1] theme.spacing[2]  /* 4px 8px */
backgroundColor: rgba(255, 255, 255, 0.15)
borderRadius: theme.borderRadius.base  /* 6px */
fontSize: theme.typography.sm
```

### Captain Rotation Pill
```css
backgroundColor: theme.colors.gold
color: #000000
fontWeight: theme.typography.semibold
```

### Goat Rotation Pill
```css
backgroundColor: rgba(220, 38, 38, 0.8)
fontWeight: theme.typography.semibold
```

### Stroke Indicator
```css
display: inline-flex
alignItems: center
justifyContent: center
width: 18px
height: 18px
backgroundColor: rgba(0, 0, 0, 0.3)
borderRadius: 50%
fontSize: 10px
fontWeight: theme.typography.bold
marginLeft: 4px

/* Half Stroke */
backgroundColor: rgba(234, 179, 8, 0.6)
```

---

## Key Improvements Summary

### 🎨 Visual Enhancements
1. **Subtle transparency layers** for team status (0.05-0.15 opacity)
2. **4px accent borders** on left side for team identification
3. **Glass effect buttons** with rgba white backgrounds
4. **Smooth transitions** (0.15s-0.3s)
5. **Box shadows** for depth on important elements

### 📐 Layout Improvements
1. **Consistent spacing scale** using theme.spacing
2. **480px max-width** for mobile-optimized layout
3. **Flex layouts** with proper gaps
4. **Fixed bottom navigation** with high z-index

### 🔤 Typography Patterns
1. **Uppercase labels** with letter-spacing (0.5px)
2. **Bold, large numbers** for scores (3xl-4xl)
3. **Semibold weights** for emphasis
4. **Text hierarchy** with distinct sizes

### 🎯 Interactive Elements
1. **48px touch targets** for navigation
2. **Hover states** with border/background changes
3. **Disabled states** with 0.3-0.4 opacity
4. **Transform scale (1.2)** for active indicators

### 🌈 Color Usage
1. **Gold** for captain/premium features
2. **Green (primary)** for positive/team1
3. **Blue (accent)** for opponent/team2
4. **Red (error)** for negative/losing states
5. **Gray scales** for neutral elements
