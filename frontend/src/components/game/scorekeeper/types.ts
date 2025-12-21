// =============================================================================
// Data Types - Live Scorekeeper
// =============================================================================

export interface PlayerStandings {
  quarters: number;
  soloCount: number;
  floatCount: number;
  optionCount: number;
}

export interface Player {
  id: string;
  name: string;
  handicap: number;
  teeOrder: number;
  standings: PlayerStandings;
}

export interface CourseHole {
  holeNumber: number;
  par: number;
  handicap: number;
  yards: number;
}

export interface Course {
  name: string;
  holes: CourseHole[];
}

export interface Game {
  id: string;
  courseName: string;
  currentHole: number;
  baseWager: number;
  status: 'in_progress' | 'completed';
  createdAt: string;
}

export interface PartnersTeam {
  type: 'partners';
  team1: string[];
  team2: string[];
}

export interface SoloTeam {
  type: 'solo';
  captain: string;
  opponents: string[];
}

export type Teams = PartnersTeam | SoloTeam;

export type BetType = 'float' | 'option' | 'duncan' | 'vinnies';

export interface Bet {
  id: string;
  type: BetType;
  invokedBy: string;
  timestamp: string;
}

export interface Hole {
  hole: number;
  par: number;
  teams: Teams;
  captainId: string;
  grossScores: Record<string, number>;
  pointsDelta: Record<string, number>;
  wager: number;
  winner: 'team1' | 'team2' | 'captain' | 'opponents' | 'push';
  bets: Bet[];
  floatInvokedBy?: string;
  optionInvokedBy?: string;
  notes: string;
}

export interface CurrentHole {
  hole: number;
  par: number;
  teamMode: 'partners' | 'solo';
  team1: string[];
  team2: string[];
  captain: string | null;
  opponents: string[];
  grossScores: Record<string, number>;
  quarters: Record<string, number>;
  wager: number;
  bets: Bet[];
  notes: string;
}

export interface BettingAction {
  id: BetType;
  label: string;
  description: string;
}

// =============================================================================
// Component Props
// =============================================================================

export interface LiveScorekeeperProps {
  game: Game;
  players: Player[];
  course: Course;
  holeHistory: Hole[];
  currentHole: CurrentHole;
  bettingActions: BettingAction[];

  // Team formation callbacks
  onToggleTeam1?: (playerId: string) => void;
  onSelectCaptain?: (playerId: string) => void;
  onSetTeamMode?: (mode: 'partners' | 'solo') => void;

  // Score entry callbacks
  onSetScore?: (playerId: string, score: number) => void;
  onSetQuarters?: (playerId: string, quarters: number) => void;

  // Betting callbacks
  onInvokeBet?: (betType: BetType, playerId: string) => void;

  // Hole management callbacks
  onSubmitHole?: () => void;
  onEditHole?: (holeNumber: number) => void;
  onSaveHoleEdit?: (hole: Hole) => void;
  onCancelEdit?: () => void;

  // Notes callback
  onSetNotes?: (notes: string) => void;

  // Player management callback
  onEditPlayerName?: (playerId: string, newName: string) => void;

  // Game completion callback
  onCompleteGame?: () => void;
}
