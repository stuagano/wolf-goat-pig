import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../../components/ui';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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

export default DatabaseManager;
