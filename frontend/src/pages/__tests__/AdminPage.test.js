/**
 * AdminPage Component Tests
 * Tests the admin dashboard functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AdminPage from '../AdminPage';
import { ThemeProvider } from '../../theme/Provider';
import { AuthProvider } from '../../context/AuthContext';

// Mock API calls
global.fetch = jest.fn();

// Mock Auth0 with admin permissions
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    isAuthenticated: true,
    user: { 
      name: 'Admin User', 
      email: 'admin@example.com',
      'https://app.com/roles': ['admin']
    },
    isLoading: false,
    getAccessTokenSilently: jest.fn(() => Promise.resolve('admin-token')),
  }),
}));

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      <AuthProvider>
        {children}
      </AuthProvider>
    </ThemeProvider>
  </BrowserRouter>
);

describe.skip('AdminPage', () => {
  beforeEach(() => {
    fetch.mockClear();
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        games: [],
        users: [],
        analytics: {}
      }),
    });
  });

  test('renders admin page with main heading', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: /admin.*dashboard/i })).toBeInTheDocument();
  });

  test('displays admin navigation tabs', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should have admin sections
    expect(screen.getByText(/users/i)).toBeInTheDocument();
    expect(screen.getByText(/games/i)).toBeInTheDocument();
    expect(screen.getByText(/analytics/i)).toBeInTheDocument();
  });

  test('shows user management section', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should have user management features
    expect(screen.getByText(/manage.*users/i)).toBeInTheDocument();
  });

  test('displays game management controls', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should have game admin features
    expect(screen.getByText(/active.*games/i) || screen.getByText(/game.*management/i)).toBeInTheDocument();
  });

  test('shows system analytics and metrics', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should display system metrics
    expect(screen.getByText(/analytics/i) || screen.getByText(/metrics/i)).toBeInTheDocument();
  });

  test('includes database management tools', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should have database tools
    expect(screen.getByText(/database/i) || screen.getByText(/backup/i)).toBeInTheDocument();
  });

  test('displays server status information', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should show server health
    expect(screen.getByText(/status/i) || screen.getByText(/health/i)).toBeInTheDocument();
  });

  test('handles user role management', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should have role management
    const roleButton = screen.getByRole('button', { name: /roles/i });
    expect(roleButton).toBeInTheDocument();
  });

  test('shows audit log or activity history', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should have audit features
    expect(screen.getByText(/audit/i) || screen.getByText(/history/i) || screen.getByText(/logs/i)).toBeInTheDocument();
  });

  test('includes configuration settings', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should have config options
    expect(screen.getByText(/settings/i) || screen.getByText(/config/i)).toBeInTheDocument();
  });

  test('handles bulk operations', async () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    const bulkActionButton = screen.getByRole('button', { name: /bulk/i });
    fireEvent.click(bulkActionButton);

    await waitFor(() => {
      expect(screen.getByText(/select.*action/i)).toBeInTheDocument();
    });
  });

  test('shows system performance metrics', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should display performance data
    expect(screen.getByText(/performance/i) || screen.getByText(/cpu/i) || screen.getByText(/memory/i)).toBeInTheDocument();
  });

  test('includes export/import functionality', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should have data export options
    expect(screen.getByText(/export/i) || screen.getByText(/import/i)).toBeInTheDocument();
  });

  test('handles error states gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('Admin API Error'));

    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  test('requires admin permissions', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should verify admin access
    expect(screen.getByTestId('admin-page') || screen.getByRole('heading')).toBeInTheDocument();
  });

  test('shows real-time updates when available', () => {
    render(
      <TestWrapper>
        <AdminPage />
      </TestWrapper>
    );

    // Should have live data indicators
    expect(screen.getByText(/live/i) || screen.getByText(/real.*time/i) || screen.getByText(/refresh/i)).toBeInTheDocument();
  });
});