import React, { useState, useEffect, useRef } from 'react';
import { Card } from './ui';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * PerformanceAnalytics - Advanced analytics visualization component
 * 
 * Features:
 * - Performance trend charts
 * - Comparative analysis
 * - Skill rating visualization
 * - Advanced metrics display
 * - Export functionality
 */
const PerformanceAnalytics = ({ playerId, playerName, timeRange = 30 }) => {
    const [trends, setTrends] = useState(null);
    const [metrics, setMetrics] = useState(null);
    const [insights, setInsights] = useState([]);
    const [skillRating, setSkillRating] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
    
    // chartRef - reserved for future chart library integration
    // eslint-disable-next-line no-unused-vars
    const chartRef = useRef(null);

    useEffect(() => {
        if (playerId) {
            loadAnalyticsData();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [playerId, selectedTimeRange]);

    const loadAnalyticsData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Load all analytics data in parallel
            const [trendsResponse, metricsResponse, insightsResponse, ratingResponse] = await Promise.all([
                fetch(`${API_URL}/api/players/${playerId}/trends?days=${selectedTimeRange}`),
                fetch(`${API_URL}/api/players/${playerId}/advanced-metrics`),
                fetch(`${API_URL}/api/players/${playerId}/insights`),
                fetch(`${API_URL}/api/players/${playerId}/skill-rating`)
            ]);

            const trendsData = trendsResponse.ok ? await trendsResponse.json() : null;
            const metricsData = metricsResponse.ok ? await metricsResponse.json() : null;
            const insightsData = insightsResponse.ok ? await insightsResponse.json() : null;
            const ratingData = ratingResponse.ok ? await ratingResponse.json() : null;

            setTrends(trendsData);
            setMetrics(metricsData);
            setInsights(insightsData?.insights || []);
            setSkillRating(ratingData);

        } catch (err) {
            setError(`Failed to load analytics data: ${err.message}`);
            console.error('Error loading analytics data:', err);
        } finally {
            setLoading(false);
        }
    };

    // Simple chart rendering function (could be replaced with a charting library)
    const renderSimpleChart = (data, title, color = '#3B82F6') => {
        // Filter out invalid data points
        const validData = (data || []).filter(d => d && typeof d.value === 'number' && !isNaN(d.value));

        if (validData.length === 0) {
            return (
                <div className="h-48 flex items-center justify-center text-gray-500">
                    No data available for {title}
                </div>
            );
        }

        const values = validData.map(d => d.value);
        const maxValue = Math.max(...values);
        const minValue = Math.min(...values);
        const range = maxValue - minValue || 1;

        return (
            <div className="h-48 relative">
                <h4 className="text-sm font-medium text-gray-700 mb-4">{title}</h4>
                <svg className="w-full h-40" viewBox="0 0 400 120">
                    {/* Grid lines */}
                    {[0, 1, 2, 3, 4].map(i => (
                        <line
                            key={i}
                            x1="0"
                            y1={i * 24}
                            x2="400"
                            y2={i * 24}
                            stroke="#f3f4f6"
                            strokeWidth="1"
                        />
                    ))}
                    
                    {/* Data line */}
                    <polyline
                        fill="none"
                        stroke={color}
                        strokeWidth="2"
                        points={validData.map((d, i) => {
                            const x = (i / Math.max(1, validData.length - 1)) * 400;
                            const y = 100 - ((d.value - minValue) / range) * 80;
                            return `${x},${y}`;
                        }).join(' ')}
                    />

                    {/* Data points */}
                    {validData.map((d, i) => {
                        const x = (i / Math.max(1, validData.length - 1)) * 400;
                        const y = 100 - ((d.value - minValue) / range) * 80;
                        return (
                            <circle
                                key={i}
                                cx={x}
                                cy={y}
                                r="3"
                                fill={color}
                                className="hover:r-4 transition-all cursor-pointer"
                                title={`${d.value.toFixed(2)} on ${d.timestamp ? new Date(d.timestamp).toLocaleDateString() : 'N/A'}`}
                            />
                        );
                    })}
                </svg>
                
                {/* Y-axis labels */}
                <div className="absolute left-0 top-0 h-40 flex flex-col justify-between text-xs text-gray-500">
                    <span>{maxValue.toFixed(1)}</span>
                    <span>{((maxValue + minValue) / 2).toFixed(1)}</span>
                    <span>{minValue.toFixed(1)}</span>
                </div>
            </div>
        );
    };

    const MetricCard = ({ title, value, change, percentile, confidence, description, color = 'blue' }) => (
        <Card className="p-4">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-600">{title}</h3>
                {percentile && (
                    <span className="text-xs text-gray-500">{percentile.toFixed(0)}th percentile</span>
                )}
            </div>
            
            <div className="flex items-center space-x-2">
                <span className={`text-2xl font-bold text-${color}-600`}>
                    {typeof value === 'number' ? value.toFixed(1) : value}
                </span>
                {change && (
                    <span className={`text-sm font-medium ${
                        change === 'improving' ? 'text-green-600' :
                        change === 'declining' ? 'text-red-600' :
                        'text-gray-600'
                    }`}>
                        {change === 'improving' ? '↗️' :
                         change === 'declining' ? '↘️' :
                         '➡️'} {change}
                    </span>
                )}
            </div>
            
            {description && (
                <p className="text-xs text-gray-500 mt-2">{description}</p>
            )}
            
            {confidence && (
                <div className="mt-2">
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                        <span>Confidence</span>
                        <span>{(confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1">
                        <div
                            className={`bg-${color}-600 h-1 rounded-full transition-all duration-300`}
                            style={{ width: `${confidence * 100}%` }}
                        ></div>
                    </div>
                </div>
            )}
        </Card>
    );

    const SkillRatingDisplay = ({ rating }) => {
        if (!rating) return null;

        const getRatingColor = (overall) => {
            if (overall >= 1600) return 'text-purple-600';
            if (overall >= 1400) return 'text-blue-600';
            if (overall >= 1200) return 'text-green-600';
            if (overall >= 1000) return 'text-yellow-600';
            return 'text-red-600';
        };

        const getRatingTier = (overall) => {
            if (overall >= 1600) return 'Master';
            if (overall >= 1400) return 'Expert';
            if (overall >= 1200) return 'Intermediate';
            if (overall >= 1000) return 'Beginner';
            return 'Novice';
        };

        return (
            <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Skill Rating</h3>
                
                <div className="text-center mb-6">
                    <div className={`text-4xl font-bold ${getRatingColor(rating.skill_rating.overall)}`}>
                        {rating.skill_rating.overall}
                    </div>
                    <div className="text-lg text-gray-600 mt-1">
                        {getRatingTier(rating.skill_rating.overall)}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                        {(rating.skill_rating.confidence * 100).toFixed(0)}% confidence
                        • {rating.skill_rating.games_played} games
                    </div>
                </div>

                <div className="space-y-3">
                    <div className="flex justify-between items-center">
                        <span className="text-gray-600">Win Rate Component</span>
                        <span className="font-semibold">{rating.skill_rating.win_component}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-gray-600">Earnings Component</span>
                        <span className="font-semibold">{rating.skill_rating.earnings_component}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-gray-600">Betting Component</span>
                        <span className="font-semibold">{rating.skill_rating.betting_component}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-gray-600">Partnership Component</span>
                        <span className="font-semibold">{rating.skill_rating.partnership_component}</span>
                    </div>
                </div>

                <div className="mt-4 pt-4 border-t">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className={`${getRatingColor(rating.skill_rating.overall).replace('text-', 'bg-')} h-2 rounded-full transition-all duration-300`}
                            style={{ width: `${Math.min(100, (rating.skill_rating.overall / 2000) * 100)}%` }}
                        ></div>
                    </div>
                </div>
            </Card>
        );
    };

    const InsightCard = ({ insight }) => {
        const getPriorityColor = (priority) => {
            switch (priority) {
                case 'high': return 'border-red-200 bg-red-50';
                case 'medium': return 'border-yellow-200 bg-yellow-50';
                case 'low': return 'border-blue-200 bg-blue-50';
                default: return 'border-gray-200 bg-gray-50';
            }
        };

        const getPriorityIcon = (priority) => {
            switch (priority) {
                case 'high': return '🔴';
                case 'medium': return '🟡';
                case 'low': return '🔵';
                default: return '⚪';
            }
        };

        return (
            <Card className={`p-4 border-2 ${getPriorityColor(insight.priority)}`}>
                <div className="flex items-start space-x-3">
                    <div className="text-xl">{getPriorityIcon(insight.priority)}</div>
                    <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-2">{insight.title}</h4>
                        <p className="text-gray-700 text-sm mb-3">{insight.description}</p>
                        
                        {insight.suggested_actions && insight.suggested_actions.length > 0 && (
                            <div>
                                <h5 className="text-xs font-medium text-gray-600 mb-2">Suggested Actions:</h5>
                                <ul className="text-xs text-gray-600 space-y-1">
                                    {insight.suggested_actions.map((action, index) => (
                                        <li key={index} className="flex items-start">
                                            <span className="mr-2">•</span>
                                            <span>{action}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            </Card>
        );
    };

    if (loading) {
        return (
            <Card className="p-6">
                <div className="text-center">
                    <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading performance analytics...</p>
                </div>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="p-6 bg-red-50 border-red-200">
                <div className="text-center">
                    <div className="w-12 h-12 text-red-500 mx-auto mb-4">⚠️</div>
                    <h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Analytics</h3>
                    <p className="text-red-600 mb-4">{error}</p>
                    <button
                        onClick={loadAnalyticsData}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                        Retry
                    </button>
                </div>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header with Time Range Selector */}
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                    {playerName ? `${playerName}'s Performance Analytics` : 'Performance Analytics'}
                </h2>
                <div className="flex space-x-2">
                    {[7, 30, 90, 365].map((days) => (
                        <button
                            key={days}
                            onClick={() => setSelectedTimeRange(days)}
                            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                                selectedTimeRange === days
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                        >
                            {days}d
                        </button>
                    ))}
                </div>
            </div>

            {/* Advanced Metrics Grid */}
            {metrics?.metrics && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Object.entries(metrics.metrics).map(([key, metric]) => (
                        <MetricCard
                            key={key}
                            title={metric.name}
                            value={metric.value}
                            change={metric.trend}
                            percentile={metric.percentile}
                            confidence={metric.confidence}
                            description={metric.description}
                            color={metric.trend === 'improving' ? 'green' : metric.trend === 'declining' ? 'red' : 'blue'}
                        />
                    ))}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Skill Rating */}
                {skillRating && (
                    <SkillRatingDisplay rating={skillRating} />
                )}

                {/* Performance Trends Charts */}
                {trends && trends.trends && (
                    <Card className="p-6">
                        <h3 className="text-lg font-semibold mb-4">Performance Trends</h3>
                        <div className="space-y-6">
                            {trends.trends.earnings && (
                                <div>
                                    {renderSimpleChart(trends.trends.earnings, 'Earnings per Game', '#10B981')}
                                </div>
                            )}
                            {trends.trends.position && (
                                <div>
                                    {renderSimpleChart(trends.trends.position, 'Position Performance', '#3B82F6')}
                                </div>
                            )}
                            {trends.trends.betting_success && (
                                <div>
                                    {renderSimpleChart(trends.trends.betting_success, 'Betting Success Rate', '#8B5CF6')}
                                </div>
                            )}
                        </div>
                    </Card>
                )}
            </div>

            {/* Insights and Recommendations */}
            {insights && insights.length > 0 && (
                <div>
                    <h3 className="text-lg font-semibold mb-4">Performance Insights</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {insights.map((insight, index) => (
                            <InsightCard key={index} insight={insight} />
                        ))}
                    </div>
                </div>
            )}

            {/* Export Options */}
            <Card className="p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h4 className="font-medium text-gray-900">Export Analytics</h4>
                        <p className="text-sm text-gray-600">Download your performance data</p>
                    </div>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => {
                                if (process.env.NODE_ENV !== 'production') {
                                    console.debug('Export to CSV (coming soon)');
                                }
                            }}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                        >
                            Export CSV
                        </button>
                        <button
                            onClick={() => {
                                if (process.env.NODE_ENV !== 'production') {
                                    console.debug('Export to PDF (coming soon)');
                                }
                            }}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Export PDF
                        </button>
                    </div>
                </div>
            </Card>
        </div>
    );
};

export default PerformanceAnalytics;
