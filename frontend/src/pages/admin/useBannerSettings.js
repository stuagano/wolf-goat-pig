import { useState } from 'react';
import { apiConfig } from '../../config/api.config';

const API_URL = apiConfig.baseUrl;

// Game banner state and API calls for the admin Banners tab.
// State lives here, owned by AdminPage, so it survives switching tabs.
export function useBannerSettings(authenticatedFetch) {
  // Banner management state
  const [bannerConfig, setBannerConfig] = useState({
    title: '',
    message: '',
    banner_type: 'info',
    is_active: true,
    background_color: '#3B82F6',
    text_color: '#FFFFFF',
    show_icon: true,
    dismissible: false
  });
  const [bannerStatus, setBannerStatus] = useState('');
  const [currentBannerId, setCurrentBannerId] = useState(null);

  // Banner management functions
  const fetchBannerConfig = async () => {
    try {
      const response = await authenticatedFetch(`${API_URL}/admin/banner`);

      if (response.ok) {
        const data = await response.json();
        if (data.banner) {
          setBannerConfig({
            title: data.banner.title || '',
            message: data.banner.message || '',
            banner_type: data.banner.banner_type || 'info',
            is_active: data.banner.is_active !== undefined ? data.banner.is_active : true,
            background_color: data.banner.background_color || '#3B82F6',
            text_color: data.banner.text_color || '#FFFFFF',
            show_icon: data.banner.show_icon !== undefined ? data.banner.show_icon : true,
            dismissible: data.banner.dismissible !== undefined ? data.banner.dismissible : false
          });
          setCurrentBannerId(data.banner.id);
        }
      }
    } catch (error) {
      console.error('Error fetching banner config:', error);
    }
  };

  const handleBannerConfigChange = (field, value) => {
    setBannerConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const saveBannerConfig = async () => {
    setBannerStatus('saving');
    try {
      const url = currentBannerId
        ? `${API_URL}/admin/banner/${currentBannerId}`
        : `${API_URL}/admin/banner`;

      const method = currentBannerId ? 'PUT' : 'POST';

      const response = await authenticatedFetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(bannerConfig)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.banner) {
          setCurrentBannerId(data.banner.id);
        }
        setBannerStatus('success');
        setTimeout(() => setBannerStatus(''), 3000);
      } else {
        setBannerStatus('error');
      }
    } catch (error) {
      console.error('Error saving banner config:', error);
      setBannerStatus('error');
    }
  };

  const deleteBanner = async () => {
    if (!currentBannerId) return;

    if (!window.confirm('Are you sure you want to delete this banner?')) return;

    setBannerStatus('deleting');
    try {
      const response = await authenticatedFetch(`${API_URL}/admin/banner/${currentBannerId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        // Reset form
        setBannerConfig({
          title: '',
          message: '',
          banner_type: 'info',
          is_active: true,
          background_color: '#3B82F6',
          text_color: '#FFFFFF',
          show_icon: true,
          dismissible: false
        });
        setCurrentBannerId(null);
        setBannerStatus('deleted');
        setTimeout(() => setBannerStatus(''), 3000);
      } else {
        setBannerStatus('error');
      }
    } catch (error) {
      console.error('Error deleting banner:', error);
      setBannerStatus('error');
    }
  };

  return {
    bannerConfig,
    bannerStatus,
    currentBannerId,
    fetchBannerConfig,
    handleBannerConfigChange,
    saveBannerConfig,
    deleteBanner,
  };
}
