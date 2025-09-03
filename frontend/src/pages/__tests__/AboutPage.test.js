/**
 * AboutPage Component Tests
 * Tests the about page functionality and content
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AboutPage from '../AboutPage';
import { ThemeProvider } from '../../theme/Provider';

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      {children}
    </ThemeProvider>
  </BrowserRouter>
);

describe('AboutPage', () => {
  test('renders about page with main heading', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: /about.*wolf.*goat.*pig/i })).toBeInTheDocument();
  });

  test('displays game description and overview', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should explain what Wolf Goat Pig is
    expect(screen.getByText(/golf.*game/i)).toBeInTheDocument();
    expect(screen.getByText(/betting/i)).toBeInTheDocument();
  });

  test('shows development team information', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should have developer/team credits
    expect(screen.getByText(/developed/i) || screen.getByText(/created/i)).toBeInTheDocument();
  });

  test('includes version information', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should show version or build info
    expect(screen.getByText(/version/i) || screen.getByText(/v\d/)).toBeInTheDocument();
  });

  test('displays contact or support information', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should have contact info
    expect(screen.getByText(/contact/i) || screen.getByText(/support/i)).toBeInTheDocument();
  });

  test('shows technology stack information', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should mention technologies used
    expect(screen.getByText(/react/i) || screen.getByText(/technology/i)).toBeInTheDocument();
  });

  test('includes navigation back to main app', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should have a way to navigate back
    const backLink = screen.getByRole('link', { name: /back/i }) ||
                    screen.getByRole('button', { name: /back/i });
    expect(backLink).toBeInTheDocument();
  });

  test('displays features and capabilities', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should list key features
    expect(screen.getByText(/features/i) || screen.getByText(/simulation/i)).toBeInTheDocument();
  });

  test('shows changelog or release notes', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should have release information
    expect(screen.getByText(/changelog/i) || screen.getByText(/updates/i) || screen.getByText(/what.*new/i)).toBeInTheDocument();
  });

  test('includes privacy policy or terms links', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should have legal/privacy info
    expect(screen.getByText(/privacy/i) || screen.getByText(/terms/i) || screen.getByText(/legal/i)).toBeInTheDocument();
  });

  test('has proper page structure and headings', () => {
    render(
      <TestWrapper>
        <AboutPage />
      </TestWrapper>
    );

    // Should have multiple headings for content sections
    const headings = screen.getAllByRole('heading');
    expect(headings.length).toBeGreaterThanOrEqual(2);
  });

  test('renders without errors', () => {
    expect(() => {
      render(
        <TestWrapper>
          <AboutPage />
        </TestWrapper>
      );
    }).not.toThrow();
  });
});