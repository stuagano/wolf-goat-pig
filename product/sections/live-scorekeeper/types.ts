// =============================================================================
// Data Types - Live Scorekeeper
// =============================================================================

export interface PlayerStandings {
  quarters: number
  soloCount: number
  floatCount: number
  optionCount: number
}

export interface Player {
  id: string
  name: string
  handicap: number
  teeOrder: number
  standings: PlayerStandings
}

export interface CourseHole {
  holeNumber: number
  par: number
  handicap: number
  yards: number
}

export interface Course {
  name: string
  holes: CourseHole[]
}

export interface Game {
  id: string
  courseName: string
  currentHole: number
  baseWager: number
  status: 'in_progress' | 'completed'
  createdAt: string
}

export interface PartnersTeam {
  type: 'partners'
  team1: string[]
  team2: string[]
}

export interface SoloTeam {
  type: 'solo'
  captain: string
  opponents: string[]
}

export type Teams = PartnersTeam | SoloTeam

export type BetType = 'float' | 'option' | 'duncan' | 'vinnies'

export interface Bet {
  id: string
  type: BetType
  invokedBy: string
  timestamp: string
}

export interface Hole {
  hole: number
  par: number
  teams: Teams
  captainId: string
  grossScores: Record<string, number>
  pointsDelta: Record<string, number>
  wager: number
  winner: 'team1' | 'team2' | 'captain' | 'opponents' | 'push'
  bets: Bet[]
  floatInvokedBy?: string
  optionInvokedBy?: string
  notes: string
}

export interface CurrentHole {
  hole: number
  par: number
  teamMode: 'partners' | 'solo'
  team1: string[]
  team2: string[]
  captain: string | null
  opponents: string[]
  grossScores: Record<string, number>
  quarters: Record<string, number>
  wager: number
  bets: Bet[]
  notes: string
}

export interface BettingAction {
  id: BetType
  label: string
  description: string
}

// =============================================================================
// Component Props
// =============================================================================

export interface LiveScorekeeperProps {
  /** The active game being played */
  game: Game
  /** Players participating in the game */
  players: Player[]
  /** Course data with hole pars and handicaps */
  course: Course
  /** History of completed holes */
  holeHistory: Hole[]
  /** The current hole being scored */
  currentHole: CurrentHole
  /** Available betting actions */
  bettingActions: BettingAction[]

  // Team formation callbacks
  /** Called when user toggles a player into/out of Team 1 */
  onToggleTeam1?: (playerId: string) => void
  /** Called when user selects a captain for solo mode */
  onSelectCaptain?: (playerId: string) => void
  /** Called when user switches between partners and solo mode */
  onSetTeamMode?: (mode: 'partners' | 'solo') => void

  // Score entry callbacks
  /** Called when user enters a gross score for a player */
  onSetScore?: (playerId: string, score: number) => void
  /** Called when user enters quarters for a player */
  onSetQuarters?: (playerId: string, quarters: number) => void

  // Betting callbacks
  /** Called when user invokes a betting action (Float, Option, etc.) */
  onInvokeBet?: (betType: BetType, playerId: string) => void

  // Hole management callbacks
  /** Called when user submits the current hole */
  onSubmitHole?: () => void
  /** Called when user wants to edit a previous hole */
  onEditHole?: (holeNumber: number) => void
  /** Called when user saves edits to a hole */
  onSaveHoleEdit?: (hole: Hole) => void
  /** Called when user cancels editing */
  onCancelEdit?: () => void

  // Notes callback
  /** Called when user updates hole notes */
  onSetNotes?: (notes: string) => void

  // Player management callback
  /** Called when user edits a player's name */
  onEditPlayerName?: (playerId: string, newName: string) => void

  // Game completion callback
  /** Called when the game is complete (after hole 18) */
  onCompleteGame?: () => void
}
