import React, { useState, useEffect } from 'react';
import { Card } from './ui';

/**
 * PlayerProfileManager - Component for managing player profiles
 * 
 * Features:
 * - Create new player profiles
 * - Edit existing profiles
 * - View profile statistics
 * - Delete/deactivate profiles
 * - Profile validation and error handling
 */
const PlayerProfileManager = ({ onProfileSelect, selectedProfile, showSelector = true }) => {
    const [profiles, setProfiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [editingProfile, setEditingProfile] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        handicap: 18.0,
        avatar_url: '',
        preferences: {
            ai_difficulty: 'medium',
            preferred_game_modes: ['wolf_goat_pig'],
            preferred_player_count: 4,
            betting_style: 'conservative',
            display_hints: true
        }
    });

    // Load profiles on component mount
    useEffect(() => {
        loadProfiles();
    }, []);

    const loadProfiles = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/players');
            if (!response.ok) {
                throw new Error('Failed to load profiles');
            }
            const data = await response.json();
            setProfiles(data);
            setError(null);
        } catch (err) {
            setError(`Failed to load profiles: ${err.message}`);
            console.error('Error loading profiles:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateProfile = async (e) => {
        e.preventDefault();
        try {
            setLoading(true);
            const response = await fetch('/api/players', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create profile');
            }

            const newProfile = await response.json();
            setProfiles([...profiles, newProfile]);
            resetForm();
            setError(null);
            
            // Auto-select the newly created profile
            if (onProfileSelect) {
                onProfileSelect(newProfile);
            }
        } catch (err) {
            setError(`Failed to create profile: ${err.message}`);
            console.error('Error creating profile:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateProfile = async (e) => {
        e.preventDefault();
        try {
            setLoading(true);
            const response = await fetch(`/api/players/${editingProfile.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update profile');
            }

            const updatedProfile = await response.json();
            setProfiles(profiles.map(p => p.id === updatedProfile.id ? updatedProfile : p));
            resetForm();
            setError(null);
        } catch (err) {
            setError(`Failed to update profile: ${err.message}`);
            console.error('Error updating profile:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteProfile = async (profileId) => {
        if (!window.confirm('Are you sure you want to delete this profile? This action cannot be undone.')) {
            return;
        }

        try {
            setLoading(true);
            const response = await fetch(`/api/players/${profileId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete profile');
            }

            setProfiles(profiles.filter(p => p.id !== profileId));
            setError(null);
            
            // Clear selection if deleted profile was selected
            if (selectedProfile && selectedProfile.id === profileId && onProfileSelect) {
                onProfileSelect(null);
            }
        } catch (err) {
            setError(`Failed to delete profile: ${err.message}`);
            console.error('Error deleting profile:', err);
        } finally {
            setLoading(false);
        }
    };

    const startEdit = (profile) => {
        setEditingProfile(profile);
        setFormData({
            name: profile.name,
            handicap: profile.handicap,
            avatar_url: profile.avatar_url || '',
            preferences: profile.preferences || formData.preferences
        });
        setShowCreateForm(true);
    };

    const resetForm = () => {
        setFormData({
            name: '',
            handicap: 18.0,
            avatar_url: '',
            preferences: {
                ai_difficulty: 'medium',
                preferred_game_modes: ['wolf_goat_pig'],
                preferred_player_count: 4,
                betting_style: 'conservative',
                display_hints: true
            }
        });
        setShowCreateForm(false);
        setEditingProfile(null);
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Never';
        try {
            return new Date(dateString).toLocaleDateString();
        } catch {
            return 'Invalid date';
        }
    };

    const getHandicapCategory = (handicap) => {
        if (handicap <= 5) return { category: 'Scratch', color: 'text-green-600' };
        if (handicap <= 12) return { category: 'Low', color: 'text-blue-600' };
        if (handicap <= 18) return { category: 'Mid', color: 'text-yellow-600' };
        if (handicap <= 25) return { category: 'High', color: 'text-orange-600' };
        return { category: 'Beginner', color: 'text-red-600' };
    };

    if (loading && profiles.length === 0) {
        return (
            <Card className="p-6">
                <div className="text-center">
                    <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading player profiles...</p>
                </div>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">Player Profiles</h2>
                <button
                    onClick={() => setShowCreateForm(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    disabled={loading}
                >
                    Create New Profile
                </button>
            </div>

            {/* Error Display */}
            {error && (
                <Card className="p-4 bg-red-50 border-red-200">
                    <div className="flex items-center">
                        <div className="w-4 h-4 text-red-500 mr-2">⚠️</div>
                        <p className="text-red-700">{error}</p>
                        <button
                            onClick={() => setError(null)}
                            className="ml-auto text-red-500 hover:text-red-700"
                        >
                            ✕
                        </button>
                    </div>
                </Card>
            )}

            {/* Create/Edit Form */}
            {showCreateForm && (
                <Card className="p-6 bg-gray-50">
                    <h3 className="text-lg font-semibold mb-4">
                        {editingProfile ? 'Edit Profile' : 'Create New Profile'}
                    </h3>
                    
                    <form onSubmit={editingProfile ? handleUpdateProfile : handleCreateProfile} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Name Field */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Player Name *
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Enter player name"
                                    required
                                    disabled={loading}
                                />
                            </div>

                            {/* Handicap Field */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Handicap *
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    max="54"
                                    step="0.1"
                                    value={formData.handicap}
                                    onChange={(e) => setFormData({ ...formData, handicap: parseFloat(e.target.value) })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    required
                                    disabled={loading}
                                />
                            </div>
                        </div>

                        {/* Avatar URL */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Avatar URL (optional)
                            </label>
                            <input
                                type="url"
                                value={formData.avatar_url}
                                onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="https://example.com/avatar.jpg"
                                disabled={loading}
                            />
                        </div>

                        {/* Preferences Section */}
                        <div className="border-t pt-4">
                            <h4 className="text-sm font-semibold text-gray-700 mb-3">Preferences</h4>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* AI Difficulty */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        AI Difficulty
                                    </label>
                                    <select
                                        value={formData.preferences.ai_difficulty}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            preferences: { ...formData.preferences, ai_difficulty: e.target.value }
                                        })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        disabled={loading}
                                    >
                                        <option value="easy">Easy</option>
                                        <option value="medium">Medium</option>
                                        <option value="hard">Hard</option>
                                    </select>
                                </div>

                                {/* Preferred Player Count */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Preferred Player Count
                                    </label>
                                    <select
                                        value={formData.preferences.preferred_player_count}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            preferences: { ...formData.preferences, preferred_player_count: parseInt(e.target.value) }
                                        })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        disabled={loading}
                                    >
                                        <option value={4}>4 Players</option>
                                        <option value={5}>5 Players</option>
                                        <option value={6}>6 Players</option>
                                    </select>
                                </div>

                                {/* Betting Style */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Betting Style
                                    </label>
                                    <select
                                        value={formData.preferences.betting_style}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            preferences: { ...formData.preferences, betting_style: e.target.value }
                                        })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        disabled={loading}
                                    >
                                        <option value="conservative">Conservative</option>
                                        <option value="moderate">Moderate</option>
                                        <option value="aggressive">Aggressive</option>
                                    </select>
                                </div>

                                {/* Display Hints */}
                                <div className="flex items-center">
                                    <input
                                        type="checkbox"
                                        id="display_hints"
                                        checked={formData.preferences.display_hints}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            preferences: { ...formData.preferences, display_hints: e.target.checked }
                                        })}
                                        className="mr-2"
                                        disabled={loading}
                                    />
                                    <label htmlFor="display_hints" className="text-sm text-gray-700">
                                        Show gameplay hints
                                    </label>
                                </div>
                            </div>
                        </div>

                        {/* Form Actions */}
                        <div className="flex space-x-3 pt-4">
                            <button
                                type="submit"
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                                disabled={loading}
                            >
                                {loading ? 'Saving...' : (editingProfile ? 'Update Profile' : 'Create Profile')}
                            </button>
                            <button
                                type="button"
                                onClick={resetForm}
                                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                                disabled={loading}
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </Card>
            )}

            {/* Profile Selector (if enabled) */}
            {showSelector && profiles.length > 0 && (
                <Card className="p-4">
                    <h3 className="text-lg font-semibold mb-3">Select Active Profile</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {profiles.map((profile) => (
                            <button
                                key={profile.id}
                                onClick={() => onProfileSelect && onProfileSelect(profile)}
                                className={`p-3 rounded-lg border-2 text-left transition-colors ${
                                    selectedProfile?.id === profile.id
                                        ? 'border-blue-500 bg-blue-50'
                                        : 'border-gray-200 hover:border-gray-300'
                                }`}
                            >
                                <div className="flex items-center space-x-3">
                                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                                        {profile.name.charAt(0).toUpperCase()}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-gray-900 truncate">{profile.name}</p>
                                        <p className="text-sm text-gray-500">Handicap: {profile.handicap}</p>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>
                </Card>
            )}

            {/* Profiles List */}
            <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">All Profiles ({profiles.length})</h3>
                
                {profiles.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        <p className="mb-4">No player profiles found.</p>
                        <button
                            onClick={() => setShowCreateForm(true)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            Create Your First Profile
                        </button>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full table-auto">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left py-2">Name</th>
                                    <th className="text-left py-2">Handicap</th>
                                    <th className="text-left py-2">Category</th>
                                    <th className="text-left py-2">Last Played</th>
                                    <th className="text-left py-2">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {profiles.map((profile) => {
                                    const handicapInfo = getHandicapCategory(profile.handicap);
                                    return (
                                        <tr key={profile.id} className="border-b hover:bg-gray-50">
                                            <td className="py-3">
                                                <div className="flex items-center space-x-3">
                                                    <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                                                        {profile.name.charAt(0).toUpperCase()}
                                                    </div>
                                                    <span className="font-medium">{profile.name}</span>
                                                    {selectedProfile?.id === profile.id && (
                                                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                                            Active
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="py-3">{profile.handicap}</td>
                                            <td className="py-3">
                                                <span className={`font-medium ${handicapInfo.color}`}>
                                                    {handicapInfo.category}
                                                </span>
                                            </td>
                                            <td className="py-3 text-gray-600">
                                                {formatDate(profile.last_played)}
                                            </td>
                                            <td className="py-3">
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={() => startEdit(profile)}
                                                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                                                        disabled={loading}
                                                    >
                                                        Edit
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteProfile(profile.id)}
                                                        className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
                                                        disabled={loading}
                                                    >
                                                        Delete
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </Card>
        </div>
    );
};

export default PlayerProfileManager;