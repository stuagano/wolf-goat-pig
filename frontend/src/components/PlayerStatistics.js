import React, { useState, useEffect } from 'react';
import { Card } from './ui';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * PlayerStatistics - Dashboard component for displaying player statistics
 * 
 * Features:
 * - Comprehensive statistics overview
 * - Performance metrics and trends
 * - Achievements display
 * - Comparative analysis
 * - Export functionality
 */
const PlayerStatistics = ({ playerId, playerName }) => {
    const [statistics, setStatistics] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    // achievements - populated by loadPlayerData for future use
    // eslint-disable-next-line no-unused-vars
    const [achievements, setAchievements] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        if (playerId) {
            loadPlayerData();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [playerId]);

    const loadPlayerData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Load statistics, analytics, and achievements in parallel
            const [statsResponse, analyticsResponse] = await Promise.all([
                fetch(`${API_URL}/api/players/${playerId}/statistics`),
                fetch(`${API_URL}/api/players/${playerId}/analytics`)
            ]);

            if (!statsResponse.ok) {
                throw new Error('Failed to load player statistics');
            }
            if (!analyticsResponse.ok) {
                throw new Error('Failed to load player analytics');
            }

            const [statsData, analyticsData] = await Promise.all([
                statsResponse.json(),
                analyticsResponse.json()
            ]);

            setStatistics(statsData);
            setAnalytics(analyticsData);

            // Placeholder for achievements - would be loaded from API
            setAchievements([]);

        } catch (err) {
            setError(`Failed to load player data: ${err.message}`);
            console.error('Error loading player data:', err);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount) => {
        return amount >= 0 ? `+$${amount.toFixed(2)}` : `-$${Math.abs(amount).toFixed(2)}`;
    };

    const formatPercentage = (value) => {
        return `${(value * 100).toFixed(1)}%`;
    };

    const getPerformanceColor = (value, thresholds = { good: 0.6, average: 0.4 }) => {
        if (value >= thresholds.good) return 'text-green-600';
        if (value >= thresholds.average) return 'text-yellow-600';
        return 'text-red-600';
    };

    const StatCard = ({ title, value, subtitle, icon, color = 'text-blue-600' }) => (
        <Card className="p-4">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm font-medium text-gray-600">{title}</p>
                    <p className={`text-2xl font-bold ${color}`}>{value}</p>
                    {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
                </div>
                {icon && <div className="text-3xl">{icon}</div>}
            </div>
        </Card>
    );

    const TabButton = ({ tab, label, active, onClick }) => (
        <button
            onClick={() => onClick(tab)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                active
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
        >
            {label}
        </button>
    );

    if (loading) {
        return (
            <Card className="p-6">
                <div className="text-center">
                    <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading player statistics...</p>
                </div>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="p-6 bg-red-50 border-red-200">
                <div className="text-center">
                    <div className="w-12 h-12 text-red-500 mx-auto mb-4">⚠️</div>
                    <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Statistics</h3>
                    <p className="text-red-600 mb-4">{error}</p>
                    <button
                        onClick={loadPlayerData}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </Card>
        );
    }

    if (!statistics) {
        return (
            <Card className="p-6">
                <div className="text-center text-gray-500">
                    <p>No statistics available for this player.</p>
                </div>
            </Card>
        );
    }

    const winRate = statistics.games_played > 0 ? statistics.games_won / statistics.games_played : 0;
    const holesWinRate = statistics.holes_played > 0 ? statistics.holes_won / statistics.holes_played : 0;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                    {playerName ? `${playerName}'s Statistics` : 'Player Statistics'}
                </h2>
                <div className="flex space-x-2">
                    <TabButton
                        tab="overview"
                        label="Overview"
                        active={activeTab === 'overview'}
                        onClick={setActiveTab}
                    />
                    <TabButton
                        tab="performance"
                        label="Performance"
                        active={activeTab === 'performance'}
                        onClick={setActiveTab}
                    />
                    <TabButton
                        tab="insights"
                        label="Insights"
                        active={activeTab === 'insights'}
                        onClick={setActiveTab}
                    />
                </div>
            </div>

            {/* Overview Tab */}
            {activeTab === 'overview' && (
                <>
                    {/* Key Statistics Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <StatCard
                            title="Games Played"
                            value={statistics.games_played}
                            subtitle="Total matches"
                            icon="🎮"
                        />
                        <StatCard
                            title="Win Rate"
                            value={formatPercentage(winRate)}
                            subtitle={`${statistics.games_won} wins`}
                            icon="🏆"
                            color={getPerformanceColor(winRate)}
                        />
                        <StatCard
                            title="Total Earnings"
                            value={formatCurrency(statistics.total_earnings)}
                            subtitle={`${statistics.avg_earnings_per_hole.toFixed(2)} per hole`}
                            icon="💰"
                            color={statistics.total_earnings >= 0 ? 'text-green-600' : 'text-red-600'}
                        />
                        <StatCard
                            title="Holes Won"
                            value={`${statistics.holes_won}/${statistics.holes_played}`}
                            subtitle={formatPercentage(holesWinRate)}
                            icon="⛳"
                            color={getPerformanceColor(holesWinRate)}
                        />
                    </div>

                    {/* Detailed Statistics */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Betting Statistics */}
                        <Card className="p-6">
                            <h3 className="text-lg font-semibold mb-4">Betting Performance</h3>
                            <div className="space-y-4">
                                <div className="flex justify-between">
                                    <span className="text-gray-600">Betting Success Rate</span>
                                    <span className={`font-semibold ${getPerformanceColor(statistics.betting_success_rate)}`}>
                                        {formatPercentage(statistics.betting_success_rate)}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600">Successful Bets</span>
                                    <span className="font-semibold">{statistics.successful_bets}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600">Total Bets</span>
                                    <span className="font-semibold">{statistics.total_bets}</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${statistics.betting_success_rate * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        </Card>

                        {/* Partnership Statistics */}
                        <Card className="p-6">
                            <h3 className="text-lg font-semibold mb-4">Partnership Performance</h3>
                            <div className="space-y-4">
                                <div className="flex justify-between">
                                    <span className="text-gray-600">Partnership Success Rate</span>
                                    <span className={`font-semibold ${getPerformanceColor(statistics.partnership_success_rate)}`}>
                                        {formatPercentage(statistics.partnership_success_rate)}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600">Partnerships Won</span>
                                    <span className="font-semibold">{statistics.partnerships_won}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-600">Partnerships Formed</span>
                                    <span className="font-semibold">{statistics.partnerships_formed}</span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className="bg-green-600 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${statistics.partnership_success_rate * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        </Card>
                    </div>

                    {/* Solo Play Statistics */}
                    <Card className="p-6">
                        <h3 className="text-lg font-semibold mb-4">Solo Play Performance</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="text-center">
                                <p className="text-2xl font-bold text-purple-600">{statistics.solo_attempts}</p>
                                <p className="text-sm text-gray-600">Solo Attempts</p>
                            </div>
                            <div className="text-center">
                                <p className="text-2xl font-bold text-purple-600">{statistics.solo_wins}</p>
                                <p className="text-sm text-gray-600">Solo Wins</p>
                            </div>
                            <div className="text-center">
                                <p className={`text-2xl font-bold ${getPerformanceColor(statistics.solo_attempts > 0 ? statistics.solo_wins / statistics.solo_attempts : 0, { good: 0.3, average: 0.15 })}`}>
                                    {statistics.solo_attempts > 0 ? formatPercentage(statistics.solo_wins / statistics.solo_attempts) : '0%'}
                                </p>
                                <p className="text-sm text-gray-600">Solo Success Rate</p>
                            </div>
                        </div>
                        {statistics.solo_attempts > 0 && (
                            <div className="mt-4">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div
                                        className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${(statistics.solo_wins / statistics.solo_attempts) * 100}%` }}
                                    ></div>
                                </div>
                            </div>
                        )}
                    </Card>
                </>
            )}

            {/* Performance Tab */}
            {activeTab === 'performance' && analytics && (
                <div className="space-y-6">
                    {/* Performance Summary */}
                    <Card className="p-6">
                        <h3 className="text-lg font-semibold mb-4">Performance Summary</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <div className="text-center">
                                <p className="text-2xl font-bold text-blue-600">
                                    {analytics.performance_summary.win_rate}%
                                </p>
                                <p className="text-sm text-gray-600">Win Rate</p>
                            </div>
                            <div className="text-center">
                                <p className="text-2xl font-bold text-green-600">
                                    ${analytics.performance_summary.avg_earnings}
                                </p>
                                <p className="text-sm text-gray-600">Avg. Earnings</p>
                            </div>
                            <div className="text-center">
                                <p className="text-2xl font-bold text-yellow-600">
                                    {analytics.performance_summary.avg_position}
                                </p>
                                <p className="text-sm text-gray-600">Avg. Position</p>
                            </div>
                            <div className="text-center">
                                <p className={`text-2xl font-bold ${
                                    analytics.performance_summary.recent_form === 'Excellent' ? 'text-green-600' :
                                    analytics.performance_summary.recent_form === 'Good' ? 'text-blue-600' :
                                    analytics.performance_summary.recent_form === 'Average' ? 'text-yellow-600' :
                                    'text-red-600'
                                }`}>
                                    {analytics.performance_summary.recent_form}
                                </p>
                                <p className="text-sm text-gray-600">Recent Form</p>
                            </div>
                        </div>
                    </Card>

                    {/* Strength Analysis */}
                    <Card className="p-6">
                        <h3 className="text-lg font-semibold mb-4">Strength Analysis</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h4 className="font-medium text-gray-700 mb-3">Skill Areas</h4>
                                <div className="space-y-3">
                                    {Object.entries(analytics.strength_analysis).map(([skill, rating]) => (
                                        <div key={skill} className="flex items-center justify-between">
                                            <span className="capitalize text-gray-600">{skill.replace('_', ' ')}</span>
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                rating === 'Strong' ? 'bg-green-100 text-green-800' :
                                                rating === 'Average' ? 'bg-yellow-100 text-yellow-800' :
                                                'bg-red-100 text-red-800'
                                            }`}>
                                                {rating}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <h4 className="font-medium text-gray-700 mb-3">Comparative Ranking</h4>
                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <span className="text-gray-600">Overall Ranking</span>
                                        <span className="font-semibold">
                                            {analytics.comparative_analysis.ranking_summary || 'Unknown'}
                                        </span>
                                    </div>
                                    {analytics.comparative_analysis.earnings_percentile && (
                                        <div className="flex items-center justify-between">
                                            <span className="text-gray-600">Earnings Percentile</span>
                                            <span className="font-semibold">
                                                {analytics.comparative_analysis.earnings_percentile}th
                                            </span>
                                        </div>
                                    )}
                                    {analytics.comparative_analysis.win_rate_percentile && (
                                        <div className="flex items-center justify-between">
                                            <span className="text-gray-600">Win Rate Percentile</span>
                                            <span className="font-semibold">
                                                {analytics.comparative_analysis.win_rate_percentile}th
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>
            )}

            {/* Insights Tab */}
            {activeTab === 'insights' && analytics && (
                <div className="space-y-6">
                    {/* Improvement Recommendations */}
                    <Card className="p-6">
                        <h3 className="text-lg font-semibold mb-4">Improvement Recommendations</h3>
                        <div className="space-y-3">
                            {analytics.improvement_recommendations.map((recommendation, index) => (
                                <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                                    <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold mt-0.5">
                                        {index + 1}
                                    </div>
                                    <p className="text-gray-700">{recommendation}</p>
                                </div>
                            ))}
                        </div>
                    </Card>

                    {/* Trend Analysis */}
                    {analytics.trend_analysis.status === 'sufficient_data' && (
                        <Card className="p-6">
                            <h3 className="text-lg font-semibold mb-4">Recent Trends</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <h4 className="font-medium text-gray-700 mb-2">Earnings Trend</h4>
                                    <div className="flex items-center space-x-2">
                                        <span className={`w-3 h-3 rounded-full ${
                                            analytics.trend_analysis.earnings_trend === 'improving' ? 'bg-green-500' : 'bg-red-500'
                                        }`}></span>
                                        <span className="capitalize font-medium">
                                            {analytics.trend_analysis.earnings_trend}
                                        </span>
                                    </div>
                                </div>
                                <div>
                                    <h4 className="font-medium text-gray-700 mb-2">Position Trend</h4>
                                    <div className="flex items-center space-x-2">
                                        <span className={`w-3 h-3 rounded-full ${
                                            analytics.trend_analysis.position_trend === 'improving' ? 'bg-green-500' : 'bg-red-500'
                                        }`}></span>
                                        <span className="capitalize font-medium">
                                            {analytics.trend_analysis.position_trend}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className="mt-4">
                                <p className="text-sm text-gray-600">
                                    Analysis based on {analytics.trend_analysis.games_analyzed} recent games
                                    • Volatility: {analytics.trend_analysis.volatility}
                                </p>
                            </div>
                        </Card>
                    )}

                    {/* Achievements Placeholder */}
                    <Card className="p-6">
                        <h3 className="text-lg font-semibold mb-4">Recent Achievements</h3>
                        <div className="text-center py-8 text-gray-500">
                            <p>Achievement system coming soon!</p>
                            <p className="text-sm mt-2">Track milestones and unlock badges as you play</p>
                        </div>
                    </Card>
                </div>
            )}
        </div>
    );
};

export default PlayerStatistics;