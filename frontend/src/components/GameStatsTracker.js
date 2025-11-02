import React, { useEffect, useCallback } from 'react';
import usePlayerProfile from '../hooks/usePlayerProfile';

/**
 * GameStatsTracker - Component for tracking and recording game statistics
 * 
 * Features:
 * - Monitors game state changes
 * - Records player performance metrics
 * - Handles game completion and result submission
 * - Manages achievement notifications
 * - Provides real-time statistics updates
 */
const GameStatsTracker = ({ 
    gameState, 
    players = [], 
    onStatsUpdate, 
    onAchievementEarned,
    gameId 
}) => {
    const { recordGameResult, selectedProfile } = usePlayerProfile();
    
    // Track game progress and metrics
    const [gameMetrics, setGameMetrics] = React.useState({
        startTime: null,
        endTime: null,
        holesCompleted: 0,
        playerMetrics: {}
    });

    // Initialize tracking when game starts
    useEffect(() => {
        if (gameState?.active && !gameMetrics.startTime) {
            setGameMetrics(prev => ({
                ...prev,
                startTime: new Date().toISOString(),
                playerMetrics: initializePlayerMetrics(players)
            }));
        }
    }, [gameState?.active, players]);

    // Monitor hole completion and update metrics
    useEffect(() => {
        if (gameState?.current_hole && gameState.current_hole !== gameMetrics.holesCompleted) {
            updateHoleMetrics(gameState);
        }
    }, [gameState?.current_hole]);

    // Handle game completion
    useEffect(() => {
        if (gameState?.game_complete && !gameMetrics.endTime) {
            handleGameCompletion(gameState);
        }
    }, [gameState?.game_complete]);

    const initializePlayerMetrics = useCallback((playerList) => {
        const metrics = {};
        playerList.forEach(player => {
            metrics[player.id] = {
                name: player.name,
                profile_id: player.profile_id || null,
                handicap: parseFloat(player.handicap) || 0,
                holes_won: 0,
                total_earnings: 0,
                successful_bets: 0,
                total_bets: 0,
                partnerships_formed: 0,
                partnerships_won: 0,
                solo_attempts: 0,
                solo_wins: 0,
                hole_scores: {},
                hole_pars: {},  // Track par for each hole
                betting_history: [],
                shot_performance: {
                    excellent_shots: 0,
                    good_shots: 0,
                    average_shots: 0,
                    poor_shots: 0,
                    total_shots: 0
                },
                score_performance: {
                    eagles: 0,        // 2 or more under par
                    birdies: 0,       // 1 under par
                    pars: 0,          // Equal to par
                    bogeys: 0,        // 1 over par
                    double_bogeys: 0, // 2 over par
                    worse: 0          // 3+ over par
                }
            };
        });
        return metrics;
    }, []);

    const updateHoleMetrics = useCallback((currentGameState) => {
        if (!currentGameState?.hole_states) return;

        const currentHole = currentGameState.current_hole;
        const holeState = currentGameState.hole_states[currentHole];

        if (!holeState) return;

        setGameMetrics(prev => {
            const updated = { ...prev };
            updated.holesCompleted = Math.max(updated.holesCompleted, currentHole);

            // Update player metrics based on hole results
            Object.entries(updated.playerMetrics).forEach(([playerId, metrics]) => {
                // Track hole results and score performance
                if (holeState.scores && holeState.scores[playerId]) {
                    const score = holeState.scores[playerId];
                    const holePar = holeState.par || currentGameState.hole_par || 4;

                    metrics.hole_scores[currentHole] = score;
                    metrics.hole_pars[currentHole] = holePar;

                    // Calculate score performance category
                    const diff = score - holePar;
                    if (diff <= -2) {
                        metrics.score_performance.eagles += 1;
                    } else if (diff === -1) {
                        metrics.score_performance.birdies += 1;
                    } else if (diff === 0) {
                        metrics.score_performance.pars += 1;
                    } else if (diff === 1) {
                        metrics.score_performance.bogeys += 1;
                    } else if (diff === 2) {
                        metrics.score_performance.double_bogeys += 1;
                    } else {
                        metrics.score_performance.worse += 1;
                    }
                }

                // Track earnings
                if (holeState.earnings && holeState.earnings[playerId]) {
                    metrics.total_earnings += holeState.earnings[playerId];
                }

                // Track hole wins
                if (holeState.winner === playerId || 
                    (holeState.team_results && holeState.team_results.winning_team?.includes(playerId))) {
                    metrics.holes_won += 1;
                }

                // Track betting results
                if (holeState.betting_results && holeState.betting_results[playerId]) {
                    const bettingResult = holeState.betting_results[playerId];
                    metrics.total_bets += bettingResult.bets_made || 0;
                    metrics.successful_bets += bettingResult.successful_bets || 0;
                    
                    // Store betting history
                    if (bettingResult.decisions) {
                        metrics.betting_history.push({
                            hole: currentHole,
                            decisions: bettingResult.decisions,
                            outcome: bettingResult.outcome,
                            earnings: bettingResult.earnings || 0
                        });
                    }
                }

                // Track partnerships
                if (holeState.teams && holeState.teams.type !== 'pending') {
                    if (holeState.teams.partnerships && holeState.teams.partnerships[playerId]) {
                        metrics.partnerships_formed += 1;
                        if (holeState.team_results?.winning_team?.includes(playerId)) {
                            metrics.partnerships_won += 1;
                        }
                    }
                    
                    // Track solo attempts
                    if (holeState.teams.solo_player === playerId) {
                        metrics.solo_attempts += 1;
                        if (holeState.team_results?.winner === playerId) {
                            metrics.solo_wins += 1;
                        }
                    }
                }

                // Track shot performance
                if (holeState.shot_results && holeState.shot_results[playerId]) {
                    holeState.shot_results[playerId].forEach(shot => {
                        metrics.shot_performance.total_shots += 1;
                        switch (shot.quality) {
                            case 'excellent':
                                metrics.shot_performance.excellent_shots += 1;
                                break;
                            case 'good':
                                metrics.shot_performance.good_shots += 1;
                                break;
                            case 'average':
                                metrics.shot_performance.average_shots += 1;
                                break;
                            default:
                                metrics.shot_performance.poor_shots += 1;
                        }
                    });
                }
            });

            return updated;
        });

        // Notify parent component of stats update
        if (onStatsUpdate) {
            onStatsUpdate(gameMetrics.playerMetrics);
        }
    }, [onStatsUpdate]);

    const handleGameCompletion = useCallback(async (finalGameState) => {
        try {
            setGameMetrics(prev => ({
                ...prev,
                endTime: new Date().toISOString()
            }));

            // Calculate final positions and submit results
            const finalResults = calculateFinalResults(finalGameState);
            
            // Submit results for players with profiles
            const submissionPromises = finalResults.map(async (result, index) => {
                const playerMetrics = gameMetrics.playerMetrics[result.player_id];
                
                if (playerMetrics && playerMetrics.profile_id) {
                    const gameResult = {
                        game_record_id: 1, // This would need to be created first
                        player_profile_id: playerMetrics.profile_id,
                        player_name: playerMetrics.name,
                        final_position: index + 1,
                        total_earnings: playerMetrics.total_earnings,
                        holes_won: playerMetrics.holes_won,
                        successful_bets: playerMetrics.successful_bets,
                        total_bets: playerMetrics.total_bets,
                        partnerships_formed: playerMetrics.partnerships_formed,
                        partnerships_won: playerMetrics.partnerships_won,
                        solo_attempts: playerMetrics.solo_attempts,
                        solo_wins: playerMetrics.solo_wins,
                        hole_scores: playerMetrics.hole_scores,
                        betting_history: playerMetrics.betting_history,
                        performance_metrics: {
                            shot_performance: playerMetrics.shot_performance,
                            score_performance: playerMetrics.score_performance,
                            hole_pars: playerMetrics.hole_pars,
                            game_duration_minutes: calculateGameDuration(),
                            course_name: finalGameState.course_name || 'Unknown'
                        }
                    };

                    try {
                        const result = await recordGameResult(gameResult);
                        
                        // Handle achievements
                        if (result.achievements_earned && result.achievements_earned.length > 0) {
                            if (onAchievementEarned) {
                                onAchievementEarned(playerMetrics.profile_id, result.achievements_earned);
                            }
                        }
                        
                        return result;
                    } catch (error) {
                        console.error('Error recording game result for player:', playerMetrics.name, error);
                        return null;
                    }
                }
                return null;
            });

            await Promise.allSettled(submissionPromises);
            
        } catch (error) {
            console.error('Error handling game completion:', error);
        }
    }, [gameMetrics, recordGameResult, onAchievementEarned]);

    const calculateFinalResults = (finalGameState) => {
        if (!finalGameState?.final_scores) return [];

        // Sort players by total points/earnings (descending)
        return Object.entries(finalGameState.final_scores)
            .map(([playerId, score]) => ({
                player_id: playerId,
                score: score,
                earnings: gameMetrics.playerMetrics[playerId]?.total_earnings || 0
            }))
            .sort((a, b) => {
                // Primary sort by score/points, secondary by earnings
                if (b.score !== a.score) {
                    return b.score - a.score;
                }
                return b.earnings - a.earnings;
            });
    };

    const calculateGameDuration = () => {
        if (!gameMetrics.startTime || !gameMetrics.endTime) return 0;
        
        const start = new Date(gameMetrics.startTime);
        const end = new Date(gameMetrics.endTime);
        return Math.round((end - start) / (1000 * 60)); // Duration in minutes
    };

    const getPlayerStatsForDisplay = (playerId) => {
        const metrics = gameMetrics.playerMetrics[playerId];
        if (!metrics) return null;

        return {
            name: metrics.name,
            holes_won: metrics.holes_won,
            total_earnings: metrics.total_earnings,
            betting_success_rate: metrics.total_bets > 0 ? 
                (metrics.successful_bets / metrics.total_bets) * 100 : 0,
            partnership_success_rate: metrics.partnerships_formed > 0 ? 
                (metrics.partnerships_won / metrics.partnerships_formed) * 100 : 0,
            solo_success_rate: metrics.solo_attempts > 0 ? 
                (metrics.solo_wins / metrics.solo_attempts) * 100 : 0,
            shot_accuracy: metrics.shot_performance.total_shots > 0 ? 
                ((metrics.shot_performance.excellent_shots + metrics.shot_performance.good_shots) / 
                 metrics.shot_performance.total_shots) * 100 : 0
        };
    };

    // This component doesn't render anything visible but tracks stats in the background
    return (
        <div style={{ display: 'none' }}>
            {/* Hidden component for statistics tracking */}
            <div data-testid="game-stats-tracker">
                <span data-testid="holes-completed">{gameMetrics.holesCompleted}</span>
                <span data-testid="game-active">{gameState?.active ? 'true' : 'false'}</span>
                <span data-testid="game-complete">{gameState?.game_complete ? 'true' : 'false'}</span>
                {Object.keys(gameMetrics.playerMetrics).map(playerId => (
                    <div key={playerId} data-testid={`player-stats-${playerId}`}>
                        {JSON.stringify(getPlayerStatsForDisplay(playerId))}
                    </div>
                ))}
            </div>
        </div>
    );
};

// Hook for easy access to game statistics
export const useGameStats = (gameState, players) => {
    const [stats, setStats] = React.useState({});
    const [achievements, setAchievements] = React.useState([]);

    const handleStatsUpdate = useCallback((playerMetrics) => {
        setStats(playerMetrics);
    }, []);

    const handleAchievementEarned = useCallback((playerId, achievementList) => {
        setAchievements(prev => [...prev, { playerId, achievements: achievementList, timestamp: Date.now() }]);
        
        // Auto-clear achievements after 5 seconds
        setTimeout(() => {
            setAchievements(prev => prev.filter(a => a.timestamp !== Date.now()));
        }, 5000);
    }, []);

    return {
        stats,
        achievements,
        handleStatsUpdate,
        handleAchievementEarned
    };
};

export default GameStatsTracker;