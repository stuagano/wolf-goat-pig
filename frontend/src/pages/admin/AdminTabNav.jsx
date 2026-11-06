import React from 'react';
import { useNavigate } from 'react-router-dom';

const AdminTabNav = ({ activeTab, setActiveTab }) => {
  const navigate = useNavigate();

  return (
    <div className="flex space-x-1 mb-8 bg-gray-200 p-1 rounded-lg">
      <button
        onClick={() => setActiveTab('email')}
        className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
          activeTab === 'email'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        📧 Email Settings
      </button>
      <button
        onClick={() => setActiveTab('sheets')}
        className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
          activeTab === 'sheets'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        📊 Sheets Integration
      </button>
                  <button
                    onClick={() => setActiveTab('database')}
                    className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
                      activeTab === 'database'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    🗃️ Database
                  </button>
                  <button
                    onClick={() => setActiveTab('ghin')}
                    className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
                      activeTab === 'ghin'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    ⛳ GHIN
                  </button>
                  <button
                    onClick={() => setActiveTab('banners')}
                    className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
                      activeTab === 'banners'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >            📢 Banners
      </button>
      <button
        onClick={() => setActiveTab('foursomes')}
        className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
          activeTab === 'foursomes'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        🎲 Foursomes
      </button>
      <button
        onClick={() => setActiveTab('toggles')}
        className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
          activeTab === 'toggles'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        🚦 Toggles
      </button>
      <button
        onClick={() => setActiveTab('players')}
        className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
          activeTab === 'players'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        👤 Account links
      </button>
      <button
        onClick={() => setActiveTab('admins')}
        className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
          activeTab === 'admins'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        }`}
      >
        🔑 Admins
      </button>
      <button
        onClick={() => navigate('/admin/roster')}
        className="flex-1 px-4 py-2 rounded-md font-medium transition-colors text-gray-600 hover:text-gray-900"
      >
        👥 Roster
      </button>
    </div>
  );
};

export default AdminTabNav;
