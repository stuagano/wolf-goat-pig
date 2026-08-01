import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import usePlayerProfile from '../../../hooks/usePlayerProfile';
import ClubPlayerSection from '../ClubPlayerSection';

vi.mock('../../../hooks/usePlayerProfile', () => ({
  default: vi.fn(),
}));

vi.mock('../LegacyNameSelector', () => ({
  default: ({ allowSkip, onSelect }) => (
    <div>
      <span>selector skip: {String(allowSkip)}</span>
      <button onClick={() => onSelect('Jane Smith')}>Select Jane Smith</button>
    </div>
  ),
}));

const theme = {
  isDark: false,
  buttonStyle: {},
  colors: {
    primary: '#166534',
    success: '#166534',
    textSecondary: '#64748b',
    border: '#d1d5db',
  },
};

describe('ClubPlayerSection', () => {
  test('gives an unlinked player a non-skippable account recovery path', () => {
    usePlayerProfile.mockReturnValue({
      profile: { id: 7, legacy_name: null },
      loading: false,
      legacyNameSuggestion: 'Jane Smith',
      updateLegacyName: vi.fn(),
    });

    render(<ClubPlayerSection cardStyle={{}} sectionTitle={{}} theme={theme} />);

    expect(screen.getByText('selector skip: false')).toBeInTheDocument();
    expect(screen.getByText(/sign up and post rounds/i)).toBeInTheDocument();
  });

  test('allows a linked player to change the roster link', async () => {
    const updateLegacyName = vi.fn().mockResolvedValue({});
    usePlayerProfile.mockReturnValue({
      profile: { id: 7, legacy_name: 'Old Name' },
      loading: false,
      legacyNameSuggestion: null,
      updateLegacyName,
    });

    render(<ClubPlayerSection cardStyle={{}} sectionTitle={{}} theme={theme} />);
    expect(screen.getByText('Linked as Old Name')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Change' }));
    fireEvent.click(screen.getByRole('button', { name: 'Select Jane Smith' }));

    await waitFor(() => {
      expect(updateLegacyName).toHaveBeenCalledWith('Jane Smith');
      expect(screen.getByText('Club player linked as Jane Smith.')).toBeInTheDocument();
    });
  });
});
