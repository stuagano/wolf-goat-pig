# Application Shell Specification

## Overview
Wolf Goat Pig uses a minimal header with bottom tab bar navigation pattern, optimized for mobile use on the golf course while maintaining full desktop functionality.

## Navigation Structure

### Primary Tabs (Bottom Bar on Mobile)
- 🏠 **Home** → `/` — Landing page and quick actions
- ⚔️ **Game** → `/game` — Create new game (Game Setup)
- 🎮 **Active** → `/games/active` — Games in progress (Live Scorekeeper access)
- 🏆 **History** → `/games/completed` — Completed games (Game History)
- ••• **More** → Opens sheet with additional options

### More Sheet Items
- 📝 Sign Up Players → `/signup`
- 📊 Leaderboard → `/leaderboard`
- 🎯 Practice Mode → `/simulation`
- 🎓 Tutorial → `/tutorial`
- 📋 Rules → `/rules`
- ℹ️ About → `/about`
- 🔧 Admin → `/admin` (admin users only)

### Desktop Navigation
Horizontal nav bar with primary items as buttons, secondary items in "More" dropdown.

## User Menu
- **Location:** Top right (desktop), in "More" sheet (mobile)
- **Contents:** User name display, theme toggle, logout button
- **Auth:** Auth0 integration with mock auth for development

## Layout Pattern
- **Header:** Emerald green bar with logo, minimal controls
- **Content:** Full-width content area
- **Footer:** Bottom tab bar (mobile) or standard footer (desktop)

## Responsive Behavior
- **Desktop (>768px):** Horizontal top nav with buttons, "More" dropdown, user menu in header
- **Mobile (≤768px):** Minimal header with logo + theme toggle, bottom tab bar with 5 items, "More" sheet slides up from bottom

## Design Tokens Applied
- **Primary:** Emerald (`#047857`) — Header background, active states
- **Neutral:** Gray — Tab bar background, borders
- **Typography:** System fonts (Inter equivalent)

## Special Features
- **Offline Indicator:** Yellow badge shows when offline
- **Theme Toggle:** Sun/moon icon for light/dark mode
- **Active Indicators:** Dot above active tab, highlighted state
- **Safe Area:** Respects iOS safe area insets for bottom bar

## Design Notes
- Bottom tab bar uses native-feeling iOS/Android patterns
- "More" sheet has drag handle and smooth slide animation
- Active tab scales icon slightly for visual feedback
- Header collapses to emoji-only logo on mobile to save space
