import React from 'react';
import { Card } from '../../components/ui';

const BannerSettingsTab = ({ banner }) => {
  const {
    bannerConfig,
    handleBannerConfigChange,
    saveBannerConfig,
    bannerStatus,
    currentBannerId,
    deleteBanner,
  } = banner;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Game Banner Configuration</h2>
        <p className="text-gray-600 mb-6">
          Create and manage announcements that appear at the top of the game page. Use banners to remind players of rules, announce updates, or share important information.
        </p>

        {/* Banner Form */}
        <div className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title (Optional)
            </label>
            <input
              type="text"
              value={bannerConfig.title}
              onChange={(e) => handleBannerConfigChange('title', e.target.value)}
              placeholder="e.g., Game Update"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Message */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message <span className="text-red-500">*</span>
            </label>
            <textarea
              value={bannerConfig.message}
              onChange={(e) => handleBannerConfigChange('message', e.target.value)}
              placeholder="e.g., Remember: The Wolf must declare their team before teeing off!"
              rows={3}
              maxLength={500}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-sm text-gray-500 mt-1">
              {bannerConfig.message.length}/500 characters
            </p>
          </div>

          {/* Banner Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Banner Type
            </label>
            <select
              value={bannerConfig.banner_type}
              onChange={(e) => handleBannerConfigChange('banner_type', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="info">📢 Info</option>
              <option value="warning">⚠️ Warning</option>
              <option value="announcement">🎉 Announcement</option>
              <option value="rules">📋 Rules</option>
            </select>
          </div>

          {/* Colors */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Background Color
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="color"
                  value={bannerConfig.background_color}
                  onChange={(e) => handleBannerConfigChange('background_color', e.target.value)}
                  className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={bannerConfig.background_color}
                  onChange={(e) => handleBannerConfigChange('background_color', e.target.value)}
                  placeholder="#3B82F6"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Text Color
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="color"
                  value={bannerConfig.text_color}
                  onChange={(e) => handleBannerConfigChange('text_color', e.target.value)}
                  className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={bannerConfig.text_color}
                  onChange={(e) => handleBannerConfigChange('text_color', e.target.value)}
                  placeholder="#FFFFFF"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Options */}
          <div className="space-y-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={bannerConfig.is_active}
                onChange={(e) => handleBannerConfigChange('is_active', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Active (Display on game page)</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={bannerConfig.show_icon}
                onChange={(e) => handleBannerConfigChange('show_icon', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Show icon</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={bannerConfig.dismissible}
                onChange={(e) => handleBannerConfigChange('dismissible', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">
                Dismissible (Allow users to close the banner)
              </span>
            </label>
          </div>

          {/* Preview */}
          {bannerConfig.message && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Preview</label>
              <div
                style={{
                  backgroundColor: bannerConfig.background_color,
                  color: bannerConfig.text_color,
                  padding: '16px 20px',
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  {bannerConfig.show_icon && (
                    <span style={{ fontSize: '24px', marginRight: '12px' }}>
                      {bannerConfig.banner_type === 'info' ? '📢' :
                       bannerConfig.banner_type === 'warning' ? '⚠️' :
                       bannerConfig.banner_type === 'announcement' ? '🎉' : '📋'}
                    </span>
                  )}
                  <div>
                    {bannerConfig.title && (
                      <h3 style={{ margin: '0 0 4px 0', fontSize: '18px', fontWeight: 'bold' }}>
                        {bannerConfig.title}
                      </h3>
                    )}
                    <p style={{ margin: 0, fontSize: '15px' }}>
                      {bannerConfig.message}
                    </p>
                  </div>
                </div>
                {bannerConfig.dismissible && (
                  <span style={{ marginLeft: '12px', fontSize: '20px' }}>×</span>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              onClick={saveBannerConfig}
              disabled={!bannerConfig.message || bannerStatus === 'saving'}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {bannerStatus === 'saving' ? 'Saving...' : currentBannerId ? 'Update Banner' : 'Create Banner'}
            </button>

            {currentBannerId && (
              <button
                onClick={deleteBanner}
                disabled={bannerStatus === 'deleting'}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {bannerStatus === 'deleting' ? 'Deleting...' : 'Delete'}
              </button>
            )}
          </div>

          {/* Status Messages */}
          {bannerStatus && bannerStatus !== 'saving' && bannerStatus !== 'deleting' && (
            <div className={`p-3 rounded-lg ${
              bannerStatus === 'success' ? 'bg-green-50 text-green-700' :
              bannerStatus === 'deleted' ? 'bg-blue-50 text-blue-700' :
              'bg-red-50 text-red-700'
            }`}>
              {bannerStatus === 'success' ? '✓ Banner saved successfully!' :
               bannerStatus === 'deleted' ? '✓ Banner deleted successfully!' :
               '✗ An error occurred. Please try again.'}
            </div>
          )}
        </div>
      </Card>

      {/* Tips Card */}
      <Card className="p-6 bg-blue-50">
        <h3 className="font-semibold text-blue-900 mb-3">💡 Tips</h3>
        <ul className="list-disc list-inside space-y-2 text-sm text-blue-800">
          <li>Use the "Rules" type for game rule reminders</li>
          <li>Use "Warning" type for important notices (red/yellow color recommended)</li>
          <li>Use "Announcement" type for celebrations or new features</li>
          <li>Keep messages concise and clear (max 500 characters)</li>
          <li>Make banners dismissible if they're not critical information</li>
          <li>Only one banner can be active at a time</li>
        </ul>
      </Card>
    </div>
  );
};

export default BannerSettingsTab;
