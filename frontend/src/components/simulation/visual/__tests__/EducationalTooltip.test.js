// frontend/src/components/simulation/visual/__tests__/EducationalTooltip.test.js
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import EducationalTooltip from '../EducationalTooltip';
import ThemeProvider from '../../../../theme/Provider';

const renderWithTheme = (component) => {
  return render(<ThemeProvider>{component}</ThemeProvider>);
};

describe('EducationalTooltip', () => {
  test('renders info icon button', () => {
    renderWithTheme(
      <EducationalTooltip
        title="Test Title"
        content="Test content"
      />
    );

    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  test('shows tooltip content on hover', async () => {
    const user = userEvent.setup();

    renderWithTheme(
      <EducationalTooltip
        title="Test Title"
        content="Test content here"
      />
    );

    const button = screen.getByRole('button');
    await user.hover(button);

    await waitFor(() => {
      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByText('Test content here')).toBeInTheDocument();
    });
  });

  test('displays title in tooltip', async () => {
    const user = userEvent.setup();

    renderWithTheme(
      <EducationalTooltip
        title="Betting Odds Explanation"
        content="Content"
      />
    );

    const button = screen.getByRole('button');
    await user.hover(button);

    await waitFor(() => {
      expect(screen.getByText('Betting Odds Explanation')).toBeInTheDocument();
    });
  });

  test('allows custom placement prop', async () => {
    // eslint-disable-next-line no-unused-vars
    const user = userEvent.setup();

    renderWithTheme(
      <EducationalTooltip
        title="Title"
        content="Content"
        placement="bottom"
      />
    );

    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  test('tooltip disappears on mouse leave', async () => {
    const user = userEvent.setup();

    renderWithTheme(
      <EducationalTooltip
        title="Test Title"
        content="Test content"
      />
    );

    const button = screen.getByRole('button');

    // Hover to show tooltip
    await user.hover(button);
    await waitFor(() => {
      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    // Unhover to hide tooltip
    await user.unhover(button);

    await waitFor(() => {
      expect(screen.queryByText('Test Title')).not.toBeInTheDocument();
    });
  });

  test('handles long content gracefully', async () => {
    const user = userEvent.setup();
    const longContent = 'This is a very long content string that explains the betting odds in great detail and should wrap properly in the tooltip.';

    renderWithTheme(
      <EducationalTooltip
        title="Long Title"
        content={longContent}
      />
    );

    const button = screen.getByRole('button');
    await user.hover(button);

    await waitFor(() => {
      expect(screen.getByText(longContent)).toBeInTheDocument();
    });
  });
});
