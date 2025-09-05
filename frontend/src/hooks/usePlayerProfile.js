import { useState, useEffect, useCallback } from 'react';

/**
 * usePlayerProfile - Custom hook for player profile management
 * 
 * Features:
 * - Profile selection and persistence
 * - Local storage integration
 * - Profile statistics caching
 * - Real-time profile updates
 * - Error handling and loading states
 */
const usePlayerProfile = () => {
    const [selectedProfile, setSelectedProfile] = useState(null);
    const [profiles, setProfiles] = useState([]);
    const [profileStatistics, setProfileStatistics] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [syncStatus, setSyncStatus] = useState('idle'); // 'idle', 'syncing', 'success', 'error'

    // Storage keys
    const STORAGE_KEYS = {
        SELECTED_PROFILE: 'wgp_selected_profile',
        PROFILES_CACHE: 'wgp_profiles_cache',
        STATISTICS_CACHE: 'wgp_statistics_cache',
        LAST_SYNC: 'wgp_last_sync'
    };

    const loadInitialData = useCallback(async () => {
        try {
            setLoading(true);
            
            // Load from localStorage first for immediate UI
            loadFromLocalStorage();
            
            // Then sync with server
            await syncWithServer();
        } catch (err) {
            console.error('Error loading initial data:', err);
            setError('Failed to load player profiles');
        } finally {
            setLoading(false);
        }
    }, []); // Add dependencies array for useCallback

    // Load initial data on mount
    useEffect(() => {
        loadInitialData();
    }, [loadInitialData]);

    const loadFromLocalStorage = () => {
        try {
            // Load selected profile
            const savedProfile = localStorage.getItem(STORAGE_KEYS.SELECTED_PROFILE);
            if (savedProfile) {
                setSelectedProfile(JSON.parse(savedProfile));
            }

            // Load profiles cache
            const cachedProfiles = localStorage.getItem(STORAGE_KEYS.PROFILES_CACHE);
            if (cachedProfiles) {
                setProfiles(JSON.parse(cachedProfiles));
            }

            // Load statistics cache
            const cachedStats = localStorage.getItem(STORAGE_KEYS.STATISTICS_CACHE);
            if (cachedStats) {
                setProfileStatistics(JSON.parse(cachedStats));
            }
        } catch (err) {
            console.error('Error loading from localStorage:', err);
            // Clear corrupted data
            Object.values(STORAGE_KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
        }
    };

    const saveToLocalStorage = (key, data) => {
        try {
            localStorage.setItem(key, JSON.stringify(data));
        } catch (err) {
            console.error('Error saving to localStorage:', err);
        }
    };

    const syncWithServer = useCallback(async () => {
        try {
            setSyncStatus('syncing');
            
            // Fetch latest profiles from server
            const response = await fetch('/api/players');
            if (!response.ok) {
                throw new Error('Failed to fetch profiles from server');
            }
            
            const serverProfiles = await response.json();
            setProfiles(serverProfiles);
            saveToLocalStorage(STORAGE_KEYS.PROFILES_CACHE, serverProfiles);

            // Update selected profile if it exists on server
            if (selectedProfile) {
                const updatedProfile = serverProfiles.find(p => p.id === selectedProfile.id);
                if (updatedProfile) {
                    setSelectedProfile(updatedProfile);
                    saveToLocalStorage(STORAGE_KEYS.SELECTED_PROFILE, updatedProfile);
                }
            }

            // Mark last sync time
            localStorage.setItem(STORAGE_KEYS.LAST_SYNC, Date.now().toString());
            setSyncStatus('success');
            
            // Clear sync status after 2 seconds
            setTimeout(() => setSyncStatus('idle'), 2000);
            
        } catch (err) {
            console.error('Error syncing with server:', err);
            setSyncStatus('error');
            
            // Clear error status after 5 seconds
            setTimeout(() => setSyncStatus('idle'), 5000);
        }
    }, [selectedProfile]);

    const selectProfile = useCallback(async (profile) => {
        try {
            setSelectedProfile(profile);
            saveToLocalStorage(STORAGE_KEYS.SELECTED_PROFILE, profile);
            
            // Load statistics for the selected profile
            await loadProfileStatistics(profile.id);
            
            // Update last played on server
            await updateLastPlayed(profile.id);
            
        } catch (err) {
            console.error('Error selecting profile:', err);
            setError('Failed to select profile');
        }
    }, [loadProfileStatistics, updateLastPlayed, STORAGE_KEYS.SELECTED_PROFILE]);

    const createProfile = useCallback(async (profileData) => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch('/api/players', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profileData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create profile');
            }

            const newProfile = await response.json();
            
            // Update local state
            const updatedProfiles = [...profiles, newProfile];
            setProfiles(updatedProfiles);
            saveToLocalStorage(STORAGE_KEYS.PROFILES_CACHE, updatedProfiles);
            
            // Auto-select the new profile
            await selectProfile(newProfile);
            
            return newProfile;
            
        } catch (err) {
            console.error('Error creating profile:', err);
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [profiles, selectProfile, STORAGE_KEYS.PROFILES_CACHE]);

    const updateProfile = useCallback(async (profileId, updateData) => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`/api/players/${profileId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update profile');
            }

            const updatedProfile = await response.json();
            
            // Update local state
            const updatedProfiles = profiles.map(p => 
                p.id === profileId ? updatedProfile : p
            );
            setProfiles(updatedProfiles);
            saveToLocalStorage(STORAGE_KEYS.PROFILES_CACHE, updatedProfiles);
            
            // Update selected profile if it's the one being updated
            if (selectedProfile && selectedProfile.id === profileId) {
                setSelectedProfile(updatedProfile);
                saveToLocalStorage(STORAGE_KEYS.SELECTED_PROFILE, updatedProfile);
            }
            
            return updatedProfile;
            
        } catch (err) {
            console.error('Error updating profile:', err);
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [profiles, selectedProfile, STORAGE_KEYS.PROFILES_CACHE, STORAGE_KEYS.SELECTED_PROFILE]);

    const deleteProfile = useCallback(async (profileId) => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await fetch(`/api/players/${profileId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete profile');
            }

            // Update local state
            const updatedProfiles = profiles.filter(p => p.id !== profileId);
            setProfiles(updatedProfiles);
            saveToLocalStorage(STORAGE_KEYS.PROFILES_CACHE, updatedProfiles);
            
            // Clear selected profile if it was deleted
            if (selectedProfile && selectedProfile.id === profileId) {
                setSelectedProfile(null);
                localStorage.removeItem(STORAGE_KEYS.SELECTED_PROFILE);
            }
            
            // Remove from statistics cache
            const updatedStats = { ...profileStatistics };
            delete updatedStats[profileId];
            setProfileStatistics(updatedStats);
            saveToLocalStorage(STORAGE_KEYS.STATISTICS_CACHE, updatedStats);
            
        } catch (err) {
            console.error('Error deleting profile:', err);
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [profiles, selectedProfile, profileStatistics, STORAGE_KEYS.PROFILES_CACHE, STORAGE_KEYS.SELECTED_PROFILE, STORAGE_KEYS.STATISTICS_CACHE]);

    const loadProfileStatistics = useCallback(async (profileId) => {
        try {
            // Return cached statistics if available and recent
            const cached = profileStatistics[profileId];
            if (cached && (Date.now() - cached.loadedAt) < 300000) { // 5 minutes
                return cached.data;
            }
            
            const response = await fetch(`/api/players/${profileId}/statistics`);
            if (!response.ok) {
                // Statistics might not exist for new profiles
                return null;
            }
            
            const stats = await response.json();
            
            // Cache the statistics
            const updatedStats = {
                ...profileStatistics,
                [profileId]: {
                    data: stats,
                    loadedAt: Date.now()
                }
            };
            setProfileStatistics(updatedStats);
            saveToLocalStorage(STORAGE_KEYS.STATISTICS_CACHE, updatedStats);
            
            return stats;
            
        } catch (err) {
            console.error('Error loading profile statistics:', err);
            return null;
        }
    }, [profileStatistics, STORAGE_KEYS.STATISTICS_CACHE]);

    const updateLastPlayed = useCallback(async (profileId) => {
        try {
            await fetch(`/api/players/${profileId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    last_played: new Date().toISOString()
                })
            });
        } catch (err) {
            console.error('Error updating last played:', err);
            // Don't throw - this is not critical
        }
    }, [STORAGE_KEYS.LAST_SYNC]);

    const recordGameResult = useCallback(async (gameResult) => {
        try {
            const response = await fetch('/api/game-results', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(gameResult)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to record game result');
            }

            const result = await response.json();
            
            // Invalidate cached statistics for the player
            const updatedStats = { ...profileStatistics };
            delete updatedStats[gameResult.player_profile_id];
            setProfileStatistics(updatedStats);
            saveToLocalStorage(STORAGE_KEYS.STATISTICS_CACHE, updatedStats);
            
            return result;
            
        } catch (err) {
            console.error('Error recording game result:', err);
            setError(err.message);
            throw err;
        }
    }, [profileStatistics, STORAGE_KEYS.STATISTICS_CACHE]);

    const getProfileById = useCallback((profileId) => {
        return profiles.find(p => p.id === profileId);
    }, [profiles]);

    const getProfileByName = useCallback((name) => {
        return profiles.find(p => p.name.toLowerCase() === name.toLowerCase());
    }, [profiles]);

    const clearError = useCallback(() => {
        setError(null);
    }, []);

    const refreshProfiles = useCallback(async () => {
        await syncWithServer();
    }, [syncWithServer]);

    // Export/Import functionality
    const exportProfileData = useCallback(async (profileId) => {
        try {
            const profile = getProfileById(profileId);
            const statistics = await loadProfileStatistics(profileId);
            
            const exportData = {
                profile,
                statistics,
                exportedAt: new Date().toISOString(),
                version: '1.0'
            };
            
            // Create and download file
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `wgp-profile-${profile.name}-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
        } catch (err) {
            console.error('Error exporting profile data:', err);
            setError('Failed to export profile data');
        }
    }, [getProfileById, loadProfileStatistics, selectedProfile]);

    // Check if profile exists locally
    const hasProfiles = profiles.length > 0;
    const hasSelectedProfile = selectedProfile !== null;
    
    // Get current profile statistics
    const currentProfileStats = selectedProfile ? 
        profileStatistics[selectedProfile.id]?.data : null;

    return {
        // State
        selectedProfile,
        profiles,
        profileStatistics: currentProfileStats,
        loading,
        error,
        syncStatus,
        hasProfiles,
        hasSelectedProfile,
        
        // Actions
        selectProfile,
        createProfile,
        updateProfile,
        deleteProfile,
        loadProfileStatistics,
        recordGameResult,
        refreshProfiles,
        exportProfileData,
        clearError,
        
        // Utilities
        getProfileById,
        getProfileByName,
        syncWithServer
    };
};

export default usePlayerProfile;