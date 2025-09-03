/**
 * RulesPage Component Tests
 * Tests the rules and instructions page
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import RulesPage from '../RulesPage';
import { ThemeProvider } from '../../theme/Provider';

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      {children}
    </ThemeProvider>
  </BrowserRouter>
);

describe('RulesPage', () => {
  test('renders rules page with main heading', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: /wolf.*goat.*pig.*rules/i })).toBeInTheDocument();
  });

  test('displays game overview section', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Should have game overview
    expect(screen.getByText(/overview/i)).toBeInTheDocument();
    expect(screen.getByText(/wolf.*goat.*pig/i)).toBeInTheDocument();
  });

  test('shows basic rules sections', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Check for main rule categories
    expect(screen.getByText(/team.*formation/i)).toBeInTheDocument();
    expect(screen.getByText(/betting/i)).toBeInTheDocument();
    expect(screen.getByText(/scoring/i)).toBeInTheDocument();
  });

  test('displays Wolf Goat Pig role explanations', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Should explain the different roles
    expect(screen.getByText(/wolf/i)).toBeInTheDocument();
    expect(screen.getByText(/goat/i)).toBeInTheDocument();
    expect(screen.getByText(/pig/i)).toBeInTheDocument();
  });

  test('explains captain rotation', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    expect(screen.getByText(/captain/i)).toBeInTheDocument();
    expect(screen.getByText(/rotation/i)).toBeInTheDocument();
  });

  test('describes betting rules', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Should mention betting concepts
    expect(screen.getByText(/double/i)).toBeInTheDocument();
    expect(screen.getByText(/quarters/i)).toBeInTheDocument();
  });

  test('explains special rules', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Should mention special variations
    expect(screen.getByText(/vinnie.*variation/i) || screen.getByText(/special.*rules/i)).toBeInTheDocument();
  });

  test('shows line of scrimmage rule', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    expect(screen.getByText(/line.*scrimmage/i)).toBeInTheDocument();
  });

  test('describes hole completion rules', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    expect(screen.getByText(/hole.*complete/i) || screen.getByText(/scoring/i)).toBeInTheDocument();
  });

  test('has expandable rule sections', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Look for expand/collapse buttons
    const expandButtons = screen.getAllByRole('button');
    expect(expandButtons.length).toBeGreaterThan(0);
  });

  test('allows expanding rule details', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Find and click an expand button
    const expandButton = screen.getByRole('button', { name: /expand/i }) || 
                         screen.getAllByRole('button')[0];
    
    fireEvent.click(expandButton);

    // Should show additional details
    expect(document.body.textContent.length).toBeGreaterThan(500);
  });

  test('includes examples and scenarios', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Should have example scenarios
    expect(screen.getByText(/example/i) || screen.getByText(/scenario/i)).toBeInTheDocument();
  });

  test('shows navigation back to game', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Should have a way to get back to the game
    const backButton = screen.getByRole('link', { name: /back/i }) ||
                      screen.getByRole('button', { name: /back/i });
    expect(backButton).toBeInTheDocument();
  });

  test('displays rules in logical order', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    const content = document.body.textContent;
    
    // Overview should come before specific rules
    const overviewIndex = content.indexOf('Overview');
    const bettingIndex = content.indexOf('Betting');
    
    if (overviewIndex !== -1 && bettingIndex !== -1) {
      expect(overviewIndex).toBeLessThan(bettingIndex);
    }
  });

  test('has accessible content structure', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Should have proper heading hierarchy
    const headings = screen.getAllByRole('heading');
    expect(headings.length).toBeGreaterThan(3);
  });

  test('includes quick reference section', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Should have quick reference or summary
    expect(
      screen.getByText(/quick.*reference/i) || 
      screen.getByText(/summary/i) ||
      screen.getByText(/cheat.*sheet/i)
    ).toBeInTheDocument();
  });

  test('explains scoring system clearly', () => {
    render(
      <TestWrapper>
        <RulesPage />
      </TestWrapper>
    );

    // Should explain how points are calculated
    expect(screen.getByText(/points/i) || screen.getByText(/score/i)).toBeInTheDocument();
    expect(screen.getByText(/win/i) || screen.getByText(/lose/i)).toBeInTheDocument();
  });
});