import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui';
import SheetIntegrationDashboard from '../components/SheetIntegrationDashboard';
import WGPAnalyticsDashboard from '../components/WGPAnalyticsDashboard';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const FoursomesManager = () => {
  const [selectedDate, setSelectedDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [existingPairings, setExistingPairings] = useState(null);

  // Get next Sunday as default
  useEffect(() => {
    const today = new Date();
    const daysUntilSunday = (7 - today.getDay()) % 7 || 7;
    const nextSunday = new Date(today);
    nextSunday.setDate(today.getDate() + daysUntilSunday);
    setSelectedDate(nextSunday.toISOString().split('T')[0]);
  }, []);

  // Check for existing pairings when date changes
  useEffect(() => {
    if (selectedDate) {
      checkExistingPairings();
    }
  }, [selectedDate]);

  const checkExistingPairings = async () => {
    try {
      const response = await fetch(`${API_URL}/pairings/${selectedDate}`);
      if (response.ok) {
        const data = await response.json();
        setExistingPairings(data.exists ? data : null);
      }
    } catch (err) {
      console.error('Error checking pairings:', err);
    }
  };

  const generateFoursomes = async (force = false) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/pairings/${selectedDate}/generate?force=${force}&send_notifications=true`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        checkExistingPairings();
      } else {
        setError(data.detail || 'Failed to generate foursomes');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const deletePairings = async () => {
    if (!window.confirm('Are you sure you want to delete these foursomes?')) return;

    try {
      const response = await fetch(`${API_URL}/pairings/${selectedDate}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setExistingPairings(null);
        setResult(null);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to delete');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    }
  };

  const runSaturdayJob = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/pairings/run-saturday-job`, {
        method: 'POST'
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        setSelectedDate(data.game_date);
        checkExistingPairings();
      } else {
        setError(data.detail || 'Failed to run Saturday job');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">🎲 Sunday Foursomes Generator</h2>
        <p className="text-gray-600 mb-6">
          Generate random foursomes for Sunday games. This will email all signed-up players
          with their group assignments and send a tee time request to the pro shop.
        </p>

        {/* Date Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Game Date</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 mb-6">
          <button
            onClick={() => generateFoursomes(false)}
            disabled={loading || !selectedDate}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
          >
            {loading ? 'Generating...' : '🎲 Generate Foursomes & Send Emails'}
          </button>

          <button
            onClick={runSaturdayJob}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {loading ? 'Running...' : '📅 Run Saturday Job (Next Sunday)'}
          </button>

          {existingPairings && (
            <>
              <button
                onClick={() => generateFoursomes(true)}
                disabled={loading}
                className="px-6 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 font-medium"
              >
                🔄 Regenerate (Replace Existing)
              </button>
              <button
                onClick={deletePairings}
                disabled={loading}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 font-medium"
              >
                🗑️ Delete Foursomes
              </button>
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Success Result */}
        {result && result.success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="font-semibold text-green-800 mb-2">✓ Foursomes Generated!</h3>
            <div className="text-green-700 space-y-1">
              <p><strong>Date:</strong> {result.date}</p>
              <p><strong>Players:</strong> {result.player_count}</p>
              <p><strong>Foursomes:</strong> {result.team_count}</p>
              <p><strong>Emails Sent:</strong> {result.notifications?.sent || 0}</p>
              {result.notifications?.failed > 0 && (
                <p className="text-yellow-700"><strong>Failed:</strong> {result.notifications.failed}</p>
              )}
            </div>
          </div>
        )}
      </Card>

      {/* Existing/Generated Foursomes Display */}
      {existingPairings && existingPairings.pairings && (
        <Card className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">
              📋 Foursomes for {existingPairings.date}
            </h3>
            <div className="text-sm text-gray-500">
              Generated: {new Date(existingPairings.generated_at).toLocaleString()}
              {existingPairings.notification_sent && ' • Emails sent ✓'}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {existingPairings.pairings.teams?.map((team, idx) => (
              <div key={idx} className="p-4 bg-gray-50 rounded-lg border-2 border-green-500">
                <h4 className="font-bold text-green-700 mb-3">Group {idx + 1}</h4>
                <ul className="space-y-2">
                  {team.players?.map((player, pIdx) => (
                    <li key={pIdx} className="flex justify-between">
                      <span>{player.player_name}</span>
                      {player.handicap && (
                        <span className="text-gray-500 text-sm">{player.handicap} HCP</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {existingPairings.pairings.remaining_players?.length > 0 && (
            <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-semibold text-yellow-800 mb-2">
                Alternates ({existingPairings.pairings.remaining_players.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {existingPairings.pairings.remaining_players.map((p, idx) => (
                  <span key={idx} className="px-3 py-1 bg-yellow-200 rounded-full text-sm">
                    {p.player_name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Info Card */}
      <Card className="p-6 bg-blue-50">
        <h3 className="font-semibold text-blue-900 mb-3">ℹ️ How it works</h3>
        <ul className="list-disc list-inside space-y-2 text-sm text-blue-800">
          <li>Foursomes are generated randomly from players signed up for the selected date</li>
          <li>Each player receives an email with their group assignment</li>
          <li>A tee time request is automatically sent to the pro shop (stuagano@gmail.com)</li>
          <li>The Saturday Job auto-runs every Saturday at 2 PM for the next Sunday</li>
          <li>You can regenerate foursomes if needed (will re-send all emails)</li>
        </ul>
      </Card>
    </div>
  );
};

const DatabaseManager = () => {
  const [schemas, setSchemas] = useState([]);
  const [selectedSchema, setSelectedSchema] = useState('');
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [tableContent, setTableContent] = useState(null);
  const [loading, setLoading] = useState(''); // Can be 'schemas', 'tables', 'content'
  const [error, setError] = useState('');

  const fetchSchemas = useCallback(async () => {
    setLoading('schemas');
    setError('');
    try {
      const response = await fetch(`${API_URL}/admin/db/schemas`, {
        headers: { 'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com' }
      });
      if (!response.ok) throw new Error('Failed to fetch schemas');
      const data = await response.json();
      setSchemas(data.schemas);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading('');
    }
  }, []);

  const fetchTables = useCallback(async (schema, signal) => {
    setLoading('tables');
    setError('');
    try {
      const response = await fetch(`${API_URL}/admin/db/schemas/${schema}/tables`, {
        headers: { 'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com' },
        signal,
      });
      if (!response.ok) throw new Error('Failed to fetch tables');
      const data = await response.json();
      setTables(data.tables);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setLoading('');
    }
  }, []);

  const fetchTableContent = useCallback(async (table, signal) => {
    setLoading('content');
    setError('');
    try {
      const response = await fetch(`${API_URL}/admin/db/schemas/${selectedSchema}/tables/${table}`, {
        headers: { 'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com' },
        signal,
      });
      if (!response.ok) throw new Error('Failed to fetch table content');
      const data = await response.json();
      setTableContent(data);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setLoading('');
    }
  }, [selectedSchema]);

  useEffect(() => {
    fetchSchemas();
  }, [fetchSchemas]);

  useEffect(() => {
    const controller = new AbortController();
    if (selectedSchema) {
      fetchTables(selectedSchema, controller.signal);
    } else {
      setTables([]);
      setSelectedTable('');
      setTableContent(null);
    }
    return () => controller.abort();
  }, [selectedSchema, fetchTables]);

  useEffect(() => {
    const controller = new AbortController();
    if (selectedTable) {
      fetchTableContent(selectedTable, controller.signal);
    } else {
      setTableContent(null);
    }
    return () => controller.abort();
  }, [selectedTable, fetchTableContent]);


  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Database Management</h2>
        {error && <p className="text-red-500">{error}</p>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Schema</label>
            <select
              value={selectedSchema}
              onChange={(e) => setSelectedSchema(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading === 'schemas'}
            >
              <option value="">{loading === 'schemas' ? 'Loading...' : 'Select a schema'}</option>
              {schemas.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Table</label>
            <select
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={!selectedSchema || loading === 'tables'}
            >
              <option value="">{loading === 'tables' ? 'Loading...' : 'Select a table'}</option>
              {tables.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>
      </Card>
      {loading === 'content' && <p>Loading table content...</p>}
      {tableContent && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Table: {tableContent.table}</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {tableContent.columns.map(col => <th key={col} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{col}</th>)}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tableContent.rows.map((row, i) => (
                  <tr key={i}>
                    {tableContent.columns.map(col => <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{JSON.stringify(row[col])}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

const AdminPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('email');
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [emailConfig, setEmailConfig] = useState({
    smtp_host: '',
    smtp_port: '',
    smtp_username: '',
    smtp_password: '',
    from_email: '',
    from_name: 'Wolf Goat Pig Admin'
  });
  const [testEmail, setTestEmail] = useState('');
  const [saveStatus, setSaveStatus] = useState('');
  const [testStatus, setTestStatus] = useState('');
  
  // OAuth2 specific state
  const [emailMethod, setEmailMethod] = useState('oauth2'); // 'smtp' or 'oauth2'
  const [oauth2Status, setOauth2Status] = useState(null);
  const [oauth2Loading, setOauth2Loading] = useState(false);
  const [credentialsFile, setCredentialsFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');

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

  // Check admin access
  useEffect(() => {
    checkAdminAccess();
    if (activeTab === 'email') {
      if (emailMethod === 'smtp') {
        fetchEmailConfig();
      } else {
        fetchOAuth2Status();
      }
    } else if (activeTab === 'banners') {
      fetchBannerConfig();
    }
  }, [activeTab, emailMethod]);

  const checkAdminAccess = async () => {
    try {
      // For now, using a simple admin check - you can enhance this with proper auth
      const adminEmails = ['stuagano@gmail.com', 'admin@wgp.com'];
      const userEmail = localStorage.getItem('userEmail') || 'stuagano@gmail.com'; // Default for testing
      
      if (adminEmails.includes(userEmail)) {
        setIsAdmin(true);
      } else {
        setIsAdmin(false);
      }
    } catch (error) {
      console.error('Error checking admin access:', error);
      setIsAdmin(false);
    } finally {
      setLoading(false);
    }
  };

  const fetchEmailConfig = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/email-config`, {
        headers: {
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setEmailConfig(prev => ({
          ...prev,
          ...data.config
        }));
      }
    } catch (error) {
      console.error('Error fetching email config:', error);
    }
  };

  const handleEmailConfigChange = (field, value) => {
    setEmailConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const saveEmailConfig = async () => {
    setSaveStatus('saving');
    try {
      const response = await fetch(`${API_URL}/admin/email-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: JSON.stringify(emailConfig)
      });

      if (response.ok) {
        setSaveStatus('success');
        setTimeout(() => setSaveStatus(''), 3000);
      } else {
        setSaveStatus('error');
      }
    } catch (error) {
      console.error('Error saving email config:', error);
      setSaveStatus('error');
    }
  };

  const testEmailConfiguration = async () => {
    if (!testEmail) {
      setTestStatus('Please enter a test email address');
      return;
    }

    setTestStatus('sending');
    try {
      const response = await fetch(`${API_URL}/admin/test-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: JSON.stringify({ 
          test_email: testEmail,
          config: emailConfig 
        })
      });

      if (response.ok) {
        setTestStatus('success');
        setTimeout(() => setTestStatus(''), 5000);
      } else {
        const error = await response.text();
        setTestStatus(`error: ${error}`);
      }
    } catch (error) {
      console.error('Error testing email:', error);
      setTestStatus('error: ' + error.message);
    }
  };

  // OAuth2 functions
  const fetchOAuth2Status = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/oauth2-status`, {
        headers: {
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setOauth2Status(data.status);
      }
    } catch (error) {
      console.error('Error fetching OAuth2 status:', error);
    }
  };

  const uploadCredentialsFile = async () => {
    if (!credentialsFile) {
      setUploadStatus('Please select a credentials file');
      return;
    }

    setUploadStatus('uploading');
    try {
      const formData = new FormData();
      formData.append('file', credentialsFile);

      const response = await fetch(`${API_URL}/admin/upload-credentials`, {
        method: 'POST',
        headers: {
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: formData
      });

      if (response.ok) {
        setUploadStatus('success');
        fetchOAuth2Status(); // Refresh status
        setTimeout(() => setUploadStatus(''), 3000);
      } else {
        const error = await response.text();
        setUploadStatus(`error: ${error}`);
      }
    } catch (error) {
      console.error('Error uploading credentials:', error);
      setUploadStatus('error: ' + error.message);
    }
  };

  const startOAuth2Flow = async () => {
    setOauth2Loading(true);
    try {
      const response = await fetch(`${API_URL}/admin/oauth2-authorize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: JSON.stringify({
          from_email: emailConfig.from_email,
          from_name: emailConfig.from_name
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Listen for OAuth success message from popup
        const handleMessage = (event) => {
          if (event.data && event.data.type === 'oauth2-success') {
            window.removeEventListener('message', handleMessage);
            setOauth2Loading(false);
            fetchOAuth2Status();
            setTestStatus('OAuth2 authorization completed successfully!');
            setTimeout(() => setTestStatus(''), 3000);
          }
        };
        window.addEventListener('message', handleMessage);
        
        // Open OAuth2 URL in new window
        window.open(data.auth_url, 'oauth2', 'width=600,height=600');
        
        // Poll for completion as backup
        const pollForCompletion = setInterval(() => {
          fetchOAuth2Status();
          if (oauth2Status?.configured) {
            clearInterval(pollForCompletion);
            setOauth2Loading(false);
            window.removeEventListener('message', handleMessage);
          }
        }, 3000);
        
        // Stop polling after 2 minutes
        setTimeout(() => {
          clearInterval(pollForCompletion);
          setOauth2Loading(false);
          window.removeEventListener('message', handleMessage);
        }, 120000);
      } else {
        const error = await response.text();
        setTestStatus(`OAuth2 Error: ${error}`);
        setOauth2Loading(false);
      }
    } catch (error) {
      console.error('Error starting OAuth2 flow:', error);
      setTestStatus('OAuth2 Error: ' + error.message);
      setOauth2Loading(false);
    }
  };

  const testOAuth2Email = async () => {
    if (!testEmail) {
      setTestStatus('Please enter a test email address');
      return;
    }

    setTestStatus('sending');
    try {
      const response = await fetch(`${API_URL}/admin/oauth2-test-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: JSON.stringify({ 
          test_email: testEmail
        })
      });

      if (response.ok) {
        setTestStatus('success');
        setTimeout(() => setTestStatus(''), 5000);
      } else {
        const error = await response.text();
        setTestStatus(`error: ${error}`);
      }
    } catch (error) {
      console.error('Error testing OAuth2 email:', error);
      setTestStatus('error: ' + error.message);
    }
  };

  // Banner management functions
  const fetchBannerConfig = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/banner`, {
        headers: {
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        }
      });

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

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
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
      const response = await fetch(`${API_URL}/admin/banner/${currentBannerId}`, {
        method: 'DELETE',
        headers: {
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        }
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <Card className="p-8 text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h2>
            <p className="text-gray-600 mb-6">You don't have permission to access this page.</p>
            <button
              onClick={() => navigate('/')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go to Home
            </button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🔧 Admin Dashboard</h1>
          <p className="text-gray-600">Manage email settings, sheets integration, and analytics</p>
        </div>

        {/* Tab Navigation */}
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
                        onClick={() => setActiveTab('analytics')}
                        className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
                          activeTab === 'analytics'
                            ? 'bg-white text-blue-600 shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                      >
                        📈 Analytics
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
        </div>

        {/* Email Settings Tab */}
        {activeTab === 'email' && (
          <div className="space-y-6">
            {/* Email Method Selection */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-6">Email Configuration Method</h2>
              <div className="flex space-x-4 mb-6">
                <button
                  onClick={() => setEmailMethod('oauth2')}
                  className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                    emailMethod === 'oauth2'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <div className="text-center">
                    <h3 className="font-semibold text-lg">OAuth2 (Recommended)</h3>
                    <p className="text-sm text-gray-600 mt-2">
                      More secure, no passwords needed. Works with Gmail's latest security requirements.
                    </p>
                    <div className="mt-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        ✓ 2024 Compatible
                      </span>
                    </div>
                  </div>
                </button>
                
                <button
                  onClick={() => setEmailMethod('smtp')}
                  className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                    emailMethod === 'smtp'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <div className="text-center">
                    <h3 className="font-semibold text-lg">SMTP with App Password</h3>
                    <p className="text-sm text-gray-600 mt-2">
                      Traditional method using SMTP with app-specific passwords.
                    </p>
                    <div className="mt-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        ⚠ May be limited
                      </span>
                    </div>
                  </div>
                </button>
              </div>
            </Card>

            {/* OAuth2 Configuration */}
            {emailMethod === 'oauth2' && (
              <>
                <Card className="p-6">
                  <h2 className="text-xl font-semibold mb-6">OAuth2 Gmail Configuration</h2>
                  
                  {/* Status Display */}
                  {oauth2Status && (
                    <div className="mb-6 p-4 rounded-lg bg-gray-50">
                      <h3 className="font-semibold mb-3">Configuration Status</h3>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">OAuth2 Configured:</span>
                          <span className={`ml-2 ${oauth2Status.configured ? 'text-green-600' : 'text-red-600'}`}>
                            {oauth2Status.configured ? '✓ Yes' : '✗ No'}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Credentials File:</span>
                          <span className={`ml-2 ${oauth2Status.credentials_file_exists ? 'text-green-600' : 'text-red-600'}`}>
                            {oauth2Status.credentials_file_exists ? '✓ Uploaded' : '✗ Missing'}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Token Valid:</span>
                          <span className={`ml-2 ${oauth2Status.credentials_valid ? 'text-green-600' : 'text-red-600'}`}>
                            {oauth2Status.credentials_valid ? '✓ Valid' : '✗ Invalid'}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">From Email:</span>
                          <span className="ml-2">{oauth2Status.from_email || 'Not set'}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Step 1: Upload Credentials */}
                  <div className="mb-6">
                    <h3 className="font-semibold mb-3">Step 1: Upload Gmail Credentials File</h3>
                    <div className="space-y-4">
                      <input
                        type="file"
                        accept=".json"
                        onChange={(e) => setCredentialsFile(e.target.files[0])}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                      />
                      <button
                        onClick={uploadCredentialsFile}
                        disabled={!credentialsFile || uploadStatus === 'uploading'}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload Credentials'}
                      </button>
                      {uploadStatus && uploadStatus !== 'uploading' && (
                        <div className={`text-sm ${
                          uploadStatus === 'success' ? 'text-green-600' : 
                          uploadStatus.startsWith('error') ? 'text-red-600' : 'text-blue-600'
                        }`}>
                          {uploadStatus === 'success' ? '✓ Credentials uploaded successfully!' : uploadStatus}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Step 2: Basic Settings */}
                  <div className="mb-6">
                    <h3 className="font-semibold mb-3">Step 2: Email Settings</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">From Email</label>
                        <input
                          type="email"
                          value={emailConfig.from_email}
                          onChange={(e) => handleEmailConfigChange('from_email', e.target.value)}
                          placeholder="your-email@gmail.com"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">From Name</label>
                        <input
                          type="text"
                          value={emailConfig.from_name}
                          onChange={(e) => handleEmailConfigChange('from_name', e.target.value)}
                          placeholder="Wolf Goat Pig Admin"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Step 3: OAuth2 Authorization */}
                  <div className="mb-6">
                    <h3 className="font-semibold mb-3">Step 3: Complete OAuth2 Authorization</h3>
                    <button
                      onClick={startOAuth2Flow}
                      disabled={!oauth2Status?.credentials_file_exists || oauth2Loading}
                      className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {oauth2Loading ? 'Authorizing...' : oauth2Status?.configured ? 'Re-authorize' : 'Start OAuth2 Setup'}
                    </button>
                    <p className="text-sm text-gray-600 mt-2">
                      This will open a new window for Google authorization. 
                      {oauth2Loading && ' Please complete the authorization in the popup window...'}
                    </p>
                  </div>
                </Card>

                {/* OAuth2 Test Email */}
                <Card className="p-6">
                  <h2 className="text-xl font-semibold mb-6">Test OAuth2 Email</h2>
                  
                  <div className="flex space-x-4">
                    <input
                      type="email"
                      value={testEmail}
                      onChange={(e) => setTestEmail(e.target.value)}
                      placeholder="Enter email address to test"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      onClick={testOAuth2Email}
                      disabled={!oauth2Status?.configured || testStatus === 'sending'}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {testStatus === 'sending' ? 'Sending...' : 'Send OAuth2 Test'}
                    </button>
                  </div>
                  
                  {testStatus && testStatus !== 'sending' && (
                    <div className={`mt-4 p-4 rounded-lg ${
                      testStatus === 'success' ? 'bg-green-100 text-green-800' :
                      testStatus.startsWith('error') || testStatus.startsWith('OAuth2 Error') ? 'bg-red-100 text-red-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {testStatus === 'success' ? '✓ OAuth2 test email sent successfully!' : testStatus}
                    </div>
                  )}
                </Card>
              </>
            )}

            {/* SMTP Configuration */}
            {emailMethod === 'smtp' && (
              <>
                <Card className="p-6">
                  <h2 className="text-xl font-semibold mb-6">SMTP Configuration</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SMTP Host
                  </label>
                  <input
                    type="text"
                    value={emailConfig.smtp_host}
                    onChange={(e) => handleEmailConfigChange('smtp_host', e.target.value)}
                    placeholder="smtp.gmail.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SMTP Port
                  </label>
                  <input
                    type="text"
                    value={emailConfig.smtp_port}
                    onChange={(e) => handleEmailConfigChange('smtp_port', e.target.value)}
                    placeholder="587"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SMTP Username
                  </label>
                  <input
                    type="text"
                    value={emailConfig.smtp_username}
                    onChange={(e) => handleEmailConfigChange('smtp_username', e.target.value)}
                    placeholder="your-email@gmail.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SMTP Password / App Password
                  </label>
                  <input
                    type="password"
                    value={emailConfig.smtp_password}
                    onChange={(e) => handleEmailConfigChange('smtp_password', e.target.value)}
                    placeholder="••••••••••••••••"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    For Gmail, use an App Password instead of your regular password
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Email
                  </label>
                  <input
                    type="email"
                    value={emailConfig.from_email}
                    onChange={(e) => handleEmailConfigChange('from_email', e.target.value)}
                    placeholder="noreply@wolfgoatpig.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Name
                  </label>
                  <input
                    type="text"
                    value={emailConfig.from_name}
                    onChange={(e) => handleEmailConfigChange('from_name', e.target.value)}
                    placeholder="Wolf Goat Pig Admin"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-4">
                <button
                  onClick={saveEmailConfig}
                  disabled={saveStatus === 'saving'}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saveStatus === 'saving' ? 'Saving...' : 
                   saveStatus === 'success' ? '✓ Saved' : 
                   saveStatus === 'error' ? 'Error - Try Again' : 
                   'Save Configuration'}
                </button>
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-6">Test Email Configuration</h2>
              
              <div className="flex space-x-4">
                <input
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  placeholder="Enter email address to test"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={testEmailConfiguration}
                  disabled={testStatus === 'sending'}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {testStatus === 'sending' ? 'Sending...' : 'Send Test Email'}
                </button>
              </div>
              
              {testStatus && testStatus !== 'sending' && (
                <div className={`mt-4 p-4 rounded-lg ${
                  testStatus === 'success' ? 'bg-green-100 text-green-800' :
                  testStatus.startsWith('error') ? 'bg-red-100 text-red-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {testStatus === 'success' ? '✓ Test email sent successfully!' : testStatus}
                </div>
              )}
            </Card>
              </>
            )}

            {/* Setup Guide */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">📚 Email Setup Guide</h2>
              
              {emailMethod === 'oauth2' ? (
                <div className="space-y-6 text-sm text-gray-600">
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <h3 className="font-semibold text-blue-900 mb-2">🚀 OAuth2 Setup (Recommended)</h3>
                    <p className="text-blue-800">
                      OAuth2 is the most secure and future-proof method for sending emails via Gmail. 
                      Follow these steps to set it up:
                    </p>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">Step 1: Create Google Cloud Project & Enable Gmail API</h3>
                    <ol className="list-decimal list-inside space-y-2 mt-2 ml-4">
                      <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Google Cloud Console</a></li>
                      <li>Create a new project or select an existing one</li>
                      <li>Enable the Gmail API:
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Go to APIs & Services → Library</li>
                          <li>Search for "Gmail API" and click on it</li>
                          <li>Click "Enable"</li>
                        </ul>
                      </li>
                    </ol>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">Step 2: Create OAuth2 Credentials</h3>
                    <ol className="list-decimal list-inside space-y-2 mt-2 ml-4">
                      <li>Go to APIs & Services → Credentials</li>
                      <li>Click "Create Credentials" → "OAuth client ID"</li>
                      <li>If prompted, configure the OAuth consent screen:
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Choose "External" user type</li>
                          <li>Fill in app name: "Wolf Goat Pig"</li>
                          <li>Add your email as a developer contact</li>
                          <li>Add scopes: ../auth/gmail.send</li>
                          <li>Add your email as a test user</li>
                        </ul>
                      </li>
                      <li>For application type, choose "Desktop application"</li>
                      <li>Give it a name like "Wolf Goat Pig Email"</li>
                      <li>Click "Create"</li>
                      <li>Download the JSON credentials file</li>
                    </ol>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">Step 3: Upload & Configure</h3>
                    <ol className="list-decimal list-inside space-y-1 mt-2 ml-4">
                      <li>Upload the downloaded JSON file using the form above</li>
                      <li>Set your "From Email" and "From Name"</li>
                      <li>Click "Start OAuth2 Setup" and complete authorization</li>
                      <li>Send a test email to verify everything works</li>
                    </ol>
                  </div>
                  
                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <h4 className="font-semibold text-green-900 mb-2">✅ Benefits of OAuth2:</h4>
                    <ul className="list-disc list-inside text-green-800 space-y-1">
                      <li>More secure than passwords</li>
                      <li>Tokens automatically refresh</li>
                      <li>Complies with Google's latest security requirements</li>
                      <li>No need to manage app passwords</li>
                      <li>Better error handling and monitoring</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 text-sm text-gray-600">
                  <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                    <h4 className="font-semibold text-yellow-900 mb-2">⚠️ SMTP with App Password</h4>
                    <p className="text-yellow-800">
                      Note: Google has deprecated "Less Secure App Access" and may limit SMTP access in the future. 
                      OAuth2 is recommended for new setups.
                    </p>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">Gmail SMTP Setup:</h3>
                    <ol className="list-decimal list-inside space-y-1 mt-2">
                      <li>Enable 2-factor authentication in your Google account</li>
                      <li>Generate an App Password: Google Account → Security → 2-Step Verification → App passwords</li>
                      <li>Use smtp.gmail.com as host, port 587</li>
                      <li>Use your Gmail address as username</li>
                      <li>Use the generated App Password (not your regular password)</li>
                    </ol>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">Other Providers:</h3>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                      <li><strong>Outlook:</strong> smtp-mail.outlook.com, port 587</li>
                      <li><strong>Yahoo:</strong> smtp.mail.yahoo.com, port 587</li>
                      <li><strong>SendGrid:</strong> smtp.sendgrid.net, port 587</li>
                    </ul>
                  </div>
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Sheets Integration Tab */}
        {activeTab === 'sheets' && (
          <SheetIntegrationDashboard />
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <WGPAnalyticsDashboard />
        )}

        {/* Database Tab */}
        {activeTab === 'database' && (
          <DatabaseManager />
        )}

        {/* Foursomes Tab */}
        {activeTab === 'foursomes' && (
          <FoursomesManager />
        )}

        {/* Banners Tab */}
        {activeTab === 'banners' && (
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
        )}
      </div>
    </div>
  );
};

export default AdminPage;