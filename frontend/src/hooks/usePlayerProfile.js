import { useState, useEffect, useCallback } from 'react';
import { storage } from '../utils/storage';
import useFetchAsync from './useFetchAsync';

/**
 * usePlayerProfile - Custom hook for player profile management
 *
 * Features:
 * - Profile selection and persistence
 * - Local storage integration via storage utility
 * - Profile statistics caching
 * - Real-time profile updates
 * - Unified error handling and loading states via useFetchAsync
 */
const usePlayerProfile = () => {
    const [selectedProfile, setSelectedProfile] = useState(null);
    const [profiles, setProfiles] = useState([]);
    const [profileStatistics, setProfileStatistics] = useState({});
    const [syncStatus, setSyncStatus] = useState('idle'); // 'idle', 'syncing', 'success', 'error'

    // Use centralized fetch hook
    const { loading, error, get, post, put, del, clearError: clearFetchError } = useFetchAsync({ throwOnError: false });

    // Storage keys
    const STORAGE_KEYS = {
        SELECTED_PROFILE: 'wgp_selected_profile',
        PROFILES_CACHE: 'wgp_profiles_cache',
        STATISTICS_CACHE: 'wgp_statistics_cache',
        LAST_SYNC: 'wgp_last_sync'
    };

    const loadFromLocalStorage = useCallback(() => {
        // Load selected profile (storage.get handles errors automatically)
        const savedProfile = storage.get(STORAGE_KEYS.SELECTED_PROFILE);
        if (savedProfile) {
            setSelectedProfile(savedProfile);
        }

        // Load profiles cache
        const cachedProfiles = storage.get(STORAGE_KEYS.PROFILES_CACHE);
        if (cachedProfiles) {
            setProfiles(cachedProfiles);
        }

        // Load statistics cache
        const cachedStats = storage.get(STORAGE_KEYS.STATISTICS_CACHE);
        if (cachedStats) {
            setProfileStatistics(cachedStats);
        }
        // STORAGE_KEYS is a constant object defined in closure
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const loadProfileStatistics = useCallback(async (profileId) => {
        // Return cached statistics if available and recent
        const cached = profileStatistics[profileId];
        if (cached && (Date.now() - cached.loadedAt) < 300000) { // 5 minutes
            return cached.data;
        }

        const stats = await get(`/api/players/${profileId}/statistics`, 'Load profile statistics');

        // Statistics might not exist for new profiles
        if (!stats) {
            return null;
        }

        // Cache the statistics
        const updatedStats = {
            ...profileStatistics,
            [profileId]: {
                data: stats,
                loadedAt: Date.now()
            }
        };
        setProfileStatistics(updatedStats);
        storage.set(STORAGE_KEYS.STATISTICS_CACHE, updatedStats);

        return stats;
    }, [profileStatistics, get, STORAGE_KEYS.STATISTICS_CACHE]);

    const updateLastPlayed = useCallback(async (profileId) => {
        // Update last played (non-critical operation)
        await put(
            `/api/players/${profileId}`,
            { last_played: new Date().toISOString() },
            'Update last played'
        );
    }, [put]);

    const syncWithServer = useCallback(async () => {
        setSyncStatus('syncing');

        const serverProfiles = await get('/api/players', 'Fetch profiles from server');

        if (serverProfiles) {
            setProfiles(serverProfiles);
            storage.set(STORAGE_KEYS.PROFILES_CACHE, serverProfiles);

            // Update selected profile if it exists on server
            if (selectedProfile) {
                const updatedProfile = serverProfiles.find(p => p.id === selectedProfile.id);
                if (updatedProfile) {
                    setSelectedProfile(updatedProfile);
                    storage.set(STORAGE_KEYS.SELECTED_PROFILE, updatedProfile);
                }
            }

            // Mark last sync time
            storage.set(STORAGE_KEYS.LAST_SYNC, Date.now());
            setSyncStatus('success');

            // Clear sync status after 2 seconds
            setTimeout(() => setSyncStatus('idle'), 2000);
        } else {
            setSyncStatus('error');

            // Clear error status after 5 seconds
            setTimeout(() => setSyncStatus('idle'), 5000);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedProfile, get]);

    const loadInitialData = useCallback(async () => {
        // Load from localStorage first for immediate UI
        loadFromLocalStorage();

        // Then sync with server (loading state managed by useFetchAsync)
        await syncWithServer();
    }, [loadFromLocalStorage, syncWithServer]);

    // Load initial data on mount
    useEffect(() => {
        loadInitialData();
    }, [loadInitialData]);

    const selectProfile = useCallback(async (profile) => {
        setSelectedProfile(profile);
        storage.set(STORAGE_KEYS.SELECTED_PROFILE, profile);

        // Load statistics for the selected profile
        await loadProfileStatistics(profile.id);

        // Update last played on server
        await updateLastPlayed(profile.id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loadProfileStatistics, updateLastPlayed]);

    const createProfile = useCallback(async (profileData) => {
        const newProfile = await post('/api/players', profileData, 'Create profile');

        if (newProfile) {
            // Update local state
            const updatedProfiles = [...profiles, newProfile];
            setProfiles(updatedProfiles);
            storage.set(STORAGE_KEYS.PROFILES_CACHE, updatedProfiles);

            // Auto-select the new profile
            await selectProfile(newProfile);

            return newProfile;
        }

        return null;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [profiles, selectProfile, post]);

    const updateProfile = useCallback(async (profileId, updateData) => {
        const updatedProfile = await put(`/api/players/${profileId}`, updateData, 'Update profile');

        if (updatedProfile) {
            // Update local state
            const updatedProfiles = profiles.map(p =>
                p.id === profileId ? updatedProfile : p
            );
            setProfiles(updatedProfiles);
            storage.set(STORAGE_KEYS.PROFILES_CACHE, updatedProfiles);

            // Update selected profile if it's the one being updated
            if (selectedProfile && selectedProfile.id === profileId) {
                setSelectedProfile(updatedProfile);
                storage.set(STORAGE_KEYS.SELECTED_PROFILE, updatedProfile);
            }

            return updatedProfile;
        }

        return null;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [profiles, selectedProfile, put]);

    const deleteProfile = useCallback(async (profileId) => {
        const result = await del(`/api/players/${profileId}`, 'Delete profile');

        if (result !== null) {
            // Update local state
            const updatedProfiles = profiles.filter(p => p.id !== profileId);
            setProfiles(updatedProfiles);
            storage.set(STORAGE_KEYS.PROFILES_CACHE, updatedProfiles);

            // Clear selected profile if it was deleted
            if (selectedProfile && selectedProfile.id === profileId) {
                setSelectedProfile(null);
                storage.remove(STORAGE_KEYS.SELECTED_PROFILE);
            }

            // Remove from statistics cache
            const updatedStats = { ...profileStatistics };
            delete updatedStats[profileId];
            setProfileStatistics(updatedStats);
            storage.set(STORAGE_KEYS.STATISTICS_CACHE, updatedStats);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [profiles, selectedProfile, profileStatistics, del]);

    const recordGameResult = useCallback(async (gameResult) => {
        const result = await post('/api/game-results', gameResult, 'Record game result');

        if (result) {
            // Invalidate cached statistics for the player
            const updatedStats = { ...profileStatistics };
            delete updatedStats[gameResult.player_profile_id];
            setProfileStatistics(updatedStats);
            storage.set(STORAGE_KEYS.STATISTICS_CACHE, updatedStats);

            return result;
        }

        return null;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [profileStatistics, post]);

    const getProfileById = useCallback((profileId) => {
        return profiles.find(p => p.id === profileId);
    }, [profiles]);

    const getProfileByName = useCallback((name) => {
        return profiles.find(p => p.name.toLowerCase() === name.toLowerCase());
    }, [profiles]);

    const clearError = useCallback(() => {
        clearFetchError();
    }, [clearFetchError]);

    const refreshProfiles = useCallback(async () => {
        await syncWithServer();
    }, [syncWithServer]);

    // Export/Import functionality
    const exportProfileData = useCallback(async (profileId) => {
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
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [getProfileById, loadProfileStatistics]);

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
