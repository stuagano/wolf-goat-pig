import React, { useState } from 'react';
import { Card } from './ui';

/**
 * SheetIntegrationDashboard - Manages Google Sheets integration for metrics and leaderboards
 * 
 * Features:
 * - Sheet structure analysis
 * - Data preview and validation
 * - Column mapping configuration
 * - Data sync and migration tools
 * - Comparison reports
 */
const SheetIntegrationDashboard = () => {
    const [sheetData, setSheetData] = useState(null);
    const [columnMappings, setColumnMappings] = useState([]);
    const [leaderboard, setLeaderboard] = useState(null);
    const [comparisonReport, setComparisonReport] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('upload');

    const handleFileUpload = (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const text = e.target.result;
                    // Parse CSV data (basic implementation)
                    const lines = text.split('\n');
                    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
                    const data = [];
                    
                    for (let i = 1; i < lines.length; i++) {
                        if (lines[i].trim()) {
                            const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
                            const row = {};
                            headers.forEach((header, index) => {
                                row[header] = values[index] || '';
                            });
                            data.push(row);
                        }
                    }
                    
                    setSheetData(data);
                    analyzeSheetStructure(headers);
                    setError(null);
                } catch (err) {
                    setError(`Error parsing file: ${err.message}`);
                }
            };
            reader.readAsText(file);
        }
    };

    const analyzeSheetStructure = async (headers) => {
        try {
            setLoading(true);
            const response = await fetch('/sheet-integration/analyze-structure', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(headers),
            });

            if (response.ok) {
                const result = await response.json();
                setColumnMappings(result.column_mappings);
            } else {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
        } catch (err) {
            setError(`Error analyzing sheet structure: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const createLeaderboard = async () => {
        if (!sheetData) return;

        try {
            setLoading(true);
            const response = await fetch('/sheet-integration/create-leaderboard', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(sheetData),
            });

            if (response.ok) {
                const result = await response.json();
                setLeaderboard(result.leaderboard);
                setActiveTab('preview');
            } else {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
        } catch (err) {
            setError(`Error creating leaderboard: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const syncDataToDatabase = async () => {
        if (!sheetData) return;

        try {
            setLoading(true);
            const response = await fetch('/sheet-integration/sync-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(sheetData),
            });

            if (response.ok) {
                const result = await response.json();
                alert(`Sync completed: ${result.sync_results.players_processed} players processed, ${result.sync_results.players_created} created, ${result.sync_results.players_updated} updated`);
            } else {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
        } catch (err) {
            setError(`Error syncing data: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const compareWithDatabase = async () => {
        if (!sheetData) return;

        try {
            setLoading(true);
            const response = await fetch('/sheet-integration/compare-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(sheetData),
            });

            if (response.ok) {
                const result = await response.json();
                setComparisonReport(result.comparison_report);
                setActiveTab('comparison');
            } else {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
        } catch (err) {
            setError(`Error comparing data: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const TabButton = ({ tab, title, isActive, onClick }) => (
        <button
            onClick={onClick}
            className={`px-4 py-2 font-medium text-sm rounded-t-lg border-b-2 transition-colors ${
                isActive
                    ? 'bg-blue-50 text-blue-700 border-blue-500'
                    : 'text-gray-600 border-transparent hover:text-gray-800 hover:border-gray-300'
            }`}
        >
            {title}
        </button>
    );

    const MappingTable = ({ mappings }) => (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Sheet Column
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Database Field
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Data Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Transformation
                        </th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {mappings.map((mapping, index) => (
                        <tr key={index}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {mapping.sheet_column}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {mapping.db_field}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                    mapping.data_type === 'text' ? 'bg-blue-100 text-blue-800' :
                                    mapping.data_type === 'number' ? 'bg-green-100 text-green-800' :
                                    mapping.data_type === 'percentage' ? 'bg-yellow-100 text-yellow-800' :
                                    mapping.data_type === 'currency' ? 'bg-purple-100 text-purple-800' :
                                    'bg-gray-100 text-gray-800'
                                }`}>
                                    {mapping.data_type}
                                </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {mapping.transformation || 'None'}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );

    const LeaderboardPreview = ({ data }) => (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Rank
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Player
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Games Played
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Win Rate
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Total Earnings
                        </th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {data.slice(0, 10).map((player, index) => (
                        <tr key={index}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                #{player.rank}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {player.player_name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {player.games_played || 0}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {player.win_rate ? `${(player.win_rate * 100).toFixed(1)}%` : '0%'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ${player.total_earnings ? player.total_earnings.toFixed(2) : '0.00'}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );

    const ComparisonReport = ({ report }) => (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Database Players</h4>
                    <p className="text-2xl font-bold text-blue-600">{report.summary.database_players}</p>
                </Card>
                <Card className="p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Sheet Players</h4>
                    <p className="text-2xl font-bold text-green-600">{report.summary.sheet_players}</p>
                </Card>
                <Card className="p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Common Players</h4>
                    <p className="text-2xl font-bold text-purple-600">{report.summary.common_players}</p>
                </Card>
            </div>

            {report.summary.database_only.length > 0 && (
                <Card className="p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Players Only in Database</h4>
                    <div className="flex flex-wrap gap-2">
                        {report.summary.database_only.map((player, index) => (
                            <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
                                {player}
                            </span>
                        ))}
                    </div>
                </Card>
            )}

            {report.summary.sheet_only.length > 0 && (
                <Card className="p-4">
                    <h4 className="font-semibold text-gray-900 mb-2">Players Only in Sheet</h4>
                    <div className="flex flex-wrap gap-2">
                        {report.summary.sheet_only.map((player, index) => (
                            <span key={index} className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded">
                                {player}
                            </span>
                        ))}
                    </div>
                </Card>
            )}

            {report.detailed_comparison.length > 0 && (
                <Card className="p-4">
                    <h4 className="font-semibold text-gray-900 mb-4">Data Differences</h4>
                    <div className="space-y-4">
                        {report.detailed_comparison.slice(0, 5).map((comparison, index) => (
                            <div key={index} className="border-l-4 border-yellow-400 pl-4">
                                <h5 className="font-medium text-gray-900">{comparison.player}</h5>
                                <div className="mt-2 space-y-1">
                                    {comparison.differences.map((diff, diffIndex) => (
                                        <div key={diffIndex} className="text-sm text-gray-600">
                                            <strong>{diff.field}:</strong> Database: {diff.database_value}, Sheet: {diff.sheet_value}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                        {report.detailed_comparison.length > 5 && (
                            <p className="text-sm text-gray-500">
                                ... and {report.detailed_comparison.length - 5} more differences
                            </p>
                        )}
                    </div>
                </Card>
            )}
        </div>
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900">Google Sheets Integration</h2>
                <p className="text-gray-600 mt-2">
                    Import and sync your Google Sheets leaderboard data with the application database.
                </p>
            </div>

            {/* Error Display */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                    <div className="flex">
                        <div className="text-red-400 mr-3">⚠️</div>
                        <div>
                            <h3 className="text-sm font-medium text-red-800">Error</h3>
                            <p className="text-sm text-red-700 mt-1">{error}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Tab Navigation */}
            <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8">
                    <TabButton
                        tab="upload"
                        title="Upload Data"
                        isActive={activeTab === 'upload'}
                        onClick={() => setActiveTab('upload')}
                    />
                    <TabButton
                        tab="mappings"
                        title="Column Mappings"
                        isActive={activeTab === 'mappings'}
                        onClick={() => setActiveTab('mappings')}
                    />
                    <TabButton
                        tab="preview"
                        title="Leaderboard Preview"
                        isActive={activeTab === 'preview'}
                        onClick={() => setActiveTab('preview')}
                    />
                    <TabButton
                        tab="comparison"
                        title="Data Comparison"
                        isActive={activeTab === 'comparison'}
                        onClick={() => setActiveTab('comparison')}
                    />
                </nav>
            </div>

            {/* Tab Content */}
            {activeTab === 'upload' && (
                <Card className="p-6">
                    <h3 className="text-lg font-semibold mb-4">Upload Sheet Data</h3>
                    
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                CSV File Upload
                            </label>
                            <input
                                type="file"
                                accept=".csv"
                                onChange={handleFileUpload}
                                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                            />
                            <p className="text-sm text-gray-500 mt-1">
                                Upload a CSV file exported from your Google Sheet
                            </p>
                        </div>

                        {sheetData && (
                            <div className="mt-6">
                                <h4 className="font-medium text-gray-900 mb-2">Data Summary</h4>
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <p className="text-sm text-gray-600">
                                        <strong>Rows:</strong> {sheetData.length}<br/>
                                        <strong>Columns:</strong> {Object.keys(sheetData[0] || {}).length}<br/>
                                        <strong>Headers:</strong> {Object.keys(sheetData[0] || {}).join(', ')}
                                    </p>
                                </div>

                                <div className="mt-4 flex space-x-4">
                                    <button
                                        onClick={createLeaderboard}
                                        disabled={loading}
                                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {loading ? 'Processing...' : 'Create Leaderboard'}
                                    </button>
                                    <button
                                        onClick={compareWithDatabase}
                                        disabled={loading}
                                        className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {loading ? 'Comparing...' : 'Compare with Database'}
                                    </button>
                                    <button
                                        onClick={syncDataToDatabase}
                                        disabled={loading}
                                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {loading ? 'Syncing...' : 'Sync to Database'}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </Card>
            )}

            {activeTab === 'mappings' && (
                <Card className="p-6">
                    <h3 className="text-lg font-semibold mb-4">Column Mappings</h3>
                    {columnMappings.length > 0 ? (
                        <>
                            <p className="text-gray-600 mb-4">
                                The following columns were automatically mapped from your sheet to database fields:
                            </p>
                            <MappingTable mappings={columnMappings} />
                        </>
                    ) : (
                        <p className="text-gray-500">
                            Upload sheet data first to see column mappings.
                        </p>
                    )}
                </Card>
            )}

            {activeTab === 'preview' && (
                <Card className="p-6">
                    <h3 className="text-lg font-semibold mb-4">Leaderboard Preview</h3>
                    {leaderboard ? (
                        <>
                            <p className="text-gray-600 mb-4">
                                Preview of leaderboard created from your sheet data:
                            </p>
                            <LeaderboardPreview data={leaderboard} />
                        </>
                    ) : (
                        <p className="text-gray-500">
                            Create a leaderboard first to see the preview.
                        </p>
                    )}
                </Card>
            )}

            {activeTab === 'comparison' && (
                <Card className="p-6">
                    <h3 className="text-lg font-semibold mb-4">Data Comparison Report</h3>
                    {comparisonReport ? (
                        <ComparisonReport report={comparisonReport} />
                    ) : (
                        <p className="text-gray-500">
                            Run a comparison first to see the report.
                        </p>
                    )}
                </Card>
            )}

            {loading && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg shadow-lg">
                        <div className="flex items-center space-x-3">
                            <div className="animate-spin w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                            <span className="text-gray-700">Processing...</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SheetIntegrationDashboard;
