// =============================================================================
// Data Types - Live Scorekeeper
// Full feature parity with SimpleScorekeeper
// =============================================================================

// =============================================================================
// Core Player & Course Types
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
  handicapRank?: number; // Alias for handicap in some API responses
  yards: number;
}

export interface Course {
  id?: string;
  name: string;
  holes: CourseHole[];
}

export interface Game {
  id: string;
  courseId?: string;
  courseName: string;
  currentHole: number;
  baseWager: number;
  status: 'in_progress' | 'completed';
  createdAt?: string;
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
// Rotation & Hitting Order (API-driven)
// =============================================================================

export interface RotationPlayer {
  playerId: string;
  name: string;
  teeOrder: number;
  strokesOnHole: number; // Creecher Feature stroke allocation
  isHoepfinger: boolean; // Wolf/Goat on this hole
}

export interface RotationState {
  holeNumber: number;
  rotationOrder: RotationPlayer[];
  captainIndex: number; // Position in rotation who picks first
  isHoepfingerPhase: boolean; // Special rules active
  hoepfingerStartHole: number; // 17 for 4-man, 16 for 5-man, 13 for 6-man
  goatPlayerIndex: number | null; // Player who is "Goat" (picks last)
}

// =============================================================================
// Aardvark Mechanics (5-man and 4-man games)
// =============================================================================

export type AardvarkMode = 'none' | 'real' | 'invisible' | 'tunkarri';

export interface AardvarkState {
  mode: AardvarkMode;
  // Real Aardvark (5-man): Player sitting out each hole
  aardvarkPlayerId: string | null;
  aardvarkRotation: string[]; // Order of who sits out
  aardvarkIndex: number; // Current position in rotation
  // Invisible Aardvark (4-man): Virtual 5th player
  invisibleAardvarkHandicap: number;
  invisibleAardvarkScore: number | null;
  // Tunkarri: Special variant
  tunkarriActive: boolean;
}

// =============================================================================
// Betting State (Float, Option, Duncan, Wager)
// =============================================================================

export interface PlayerBettingUsage {
  playerId: string;
  floatUsed: boolean;
  floatHole: number | null;
  optionUsed: boolean;
  optionHole: number | null;
  duncanUsed: boolean;
  duncanHole: number | null;
}

export interface BetOffer {
  id: string;
  type: BetType;
  offeredBy: string;
  offeredTo: string[];
  status: 'pending' | 'accepted' | 'declined' | 'expired';
  timestamp: string;
}

export interface BettingState {
  playerUsage: Record<string, PlayerBettingUsage>;
  currentWager: number;
  baseWager: number;
  wagerMultiplier: number; // For doubled/tripled wagers
  // Active offers on current hole
  pendingOffers: BetOffer[];
  // Duncan specifics (3-for-2 solo)
  duncanActive: boolean;
  duncanPlayerId: string | null;
  // Vinnies (score-based multiplier)
  vinniesActive: boolean;
  vinniesMultiplier: number;
}

// =============================================================================
// Stroke Allocation (Creecher Feature)
// =============================================================================

export interface HoleStrokeAllocation {
  playerId: string;
  playerHandicap: number;
  courseHoleHandicap: number;
  fullStrokes: number; // Integer strokes
  halfStroke: boolean; // Creecher Feature half-stroke
  totalStrokes: number; // fullStrokes + (halfStroke ? 0.5 : 0)
  netScore: number | null; // grossScore - totalStrokes (calculated)
}

export interface StrokeAllocationState {
  allocations: Record<number, HoleStrokeAllocation[]>; // keyed by holeNumber
  creecherEnabled: boolean;
  displayMode: 'gross' | 'net' | 'both';
}

// =============================================================================
// Game State (Consolidated)
// =============================================================================

export interface GameState {
  game: Game;
  players: Player[];
  course: Course;
  holeHistory: Hole[];
  currentHole: CurrentHole;
  rotation: RotationState;
  aardvark: AardvarkState;
  betting: BettingState;
  strokes: StrokeAllocationState;
  // UI State
  isLoading: boolean;
  error: string | null;
  lastSavedAt: string | null;
}

// =============================================================================
// API Response Types
// =============================================================================

export interface RotationApiResponse {
  holeNumber: number;
  rotation: Array<{
    playerId: string;
    name: string;
    teeOrder: number;
  }>;
  captainIndex: number;
  isHoepfingerHole: boolean;
}

export interface WagerApiResponse {
  holeNumber: number;
  wager: number;
  baseWager: number;
  multiplier: number;
  reason?: string; // e.g., "Float doubled wager"
}

export interface SubmitHolePayload {
  gameId: string;
  holeNumber: number;
  teams: Teams;
  grossScores: Record<string, number>;
  quarters: Record<string, number>;
  wager: number;
  bets: Bet[];
  notes: string;
}

export interface SubmitHoleResponse {
  success: boolean;
  holeId: string;
  updatedStandings: Record<string, PlayerStandings>;
  nextHole: number;
  achievements?: Achievement[];
}

export interface Achievement {
  id: string;
  playerId: string;
  type: string;
  title: string;
  description: string;
  earnedAt: string;
}

// =============================================================================
// Quarters Preset Types
// =============================================================================

export interface QuartersPreset {
  id: string;
  label: string;
  description: string;
  // Function to calculate quarters given team assignments
  calculate: (
    teamMode: 'partners' | 'solo',
    team1: string[],
    team2: string[],
    captain: string | null,
    opponents: string[],
    wager: number
  ) => Record<string, number>;
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

// =============================================================================
// Container Props (LiveScorekeeperContainer)
// =============================================================================

export interface LiveScorekeeperContainerProps {
  gameId: string;
  // Initial data (loaded by parent page)
  initialPlayers?: Array<{
    id: string;
    name: string;
    handicap: number;
    tee_order?: number;
    teeOrder?: number;
    points?: number;
  }>;
  initialHoleHistory?: Array<{
    hole: number;
    par?: number;
    points_delta?: Record<string, number>;
    pointsDelta?: Record<string, number>;
    gross_scores?: Record<string, number>;
    grossScores?: Record<string, number>;
    betting_narrative?: string;
    wager?: number;
    teams?: Teams;
    captainId?: string;
  }>;
  initialCurrentHole?: number;
  courseName?: string;
  initialStrokeAllocation?: Record<string, number[]> | null;
  baseWager?: number;
  // Feature flags
  enableCreecherFeature?: boolean;
  enableAardvark?: boolean;
  enableCommissionerChat?: boolean;
  enableBadgeNotifications?: boolean;
  // Callbacks for parent page
  onGameComplete?: (finalStandings: Record<string, PlayerStandings>) => void;
  onError?: (error: Error) => void;
}

// =============================================================================
// Hook Return Types
// =============================================================================

export interface UseGameStateReturn {
  state: GameState;
  // Team actions
  toggleTeam1: (playerId: string) => void;
  selectCaptain: (playerId: string) => void;
  setTeamMode: (mode: 'partners' | 'solo') => void;
  // Score actions
  setScore: (playerId: string, score: number) => void;
  setQuarters: (playerId: string, quarters: number) => void;
  applyQuartersPreset: (presetId: string) => void;
  // Navigation
  goToHole: (holeNumber: number) => void;
  undoLastHole: () => void;
  // Notes
  setNotes: (notes: string) => void;
  // Player management
  editPlayerName: (playerId: string, newName: string) => void;
  // Validation
  validateCurrentHole: () => { isValid: boolean; errors: string[] };
}

export interface UseRotationWagerReturn {
  rotation: RotationState;
  wager: WagerApiResponse | null;
  isLoading: boolean;
  error: string | null;
  fetchRotation: (gameId: string, holeNumber: number) => Promise<void>;
  fetchWager: (gameId: string, holeNumber: number) => Promise<void>;
}

export interface UseBettingActionsReturn {
  betting: BettingState;
  // Invoke actions
  invokeFloat: (playerId: string) => void;
  invokeOption: (playerId: string) => void;
  invokeDuncan: (playerId: string) => void;
  invokeVinnies: () => void;
  // Offer/Accept flow
  offerBet: (type: BetType, toPlayerIds: string[]) => void;
  acceptOffer: (offerId: string) => void;
  declineOffer: (offerId: string) => void;
  // Queries
  canInvokeFloat: (playerId: string) => boolean;
  canInvokeOption: (playerId: string) => boolean;
  canInvokeDuncan: (playerId: string) => boolean;
  getPlayerUsage: (playerId: string) => PlayerBettingUsage;
}

export interface UseStrokeAllocationReturn {
  allocations: StrokeAllocationState;
  // Calculate for current hole
  calculateAllocations: (holeNumber: number, players: Player[], course: Course) => HoleStrokeAllocation[];
  // Get allocation for specific player on specific hole
  getPlayerAllocation: (playerId: string, holeNumber: number) => HoleStrokeAllocation | null;
  // Calculate net score
  calculateNetScore: (playerId: string, holeNumber: number, grossScore: number) => number;
  // Toggle display mode
  setDisplayMode: (mode: 'gross' | 'net' | 'both') => void;
}

export interface UseHoleSubmissionReturn {
  isSubmitting: boolean;
  error: string | null;
  // Submit current hole
  submitHole: (payload: SubmitHolePayload) => Promise<SubmitHoleResponse>;
  // Check achievements after submission
  checkAchievements: (playerId: string) => Promise<Achievement[]>;
  // Complete game
  completeGame: (gameId: string) => Promise<void>;
}

export interface UseAardvarkReturn {
  aardvark: AardvarkState;
  // Set invisible aardvark score
  setInvisibleAardvarkScore: (score: number) => void;
  // Get current aardvark player (5-man)
  getCurrentAardvark: () => string | null;
  // Advance aardvark rotation
  advanceAardvark: () => void;
  // Check if player is current aardvark
  isPlayerAardvark: (playerId: string) => boolean;
}
