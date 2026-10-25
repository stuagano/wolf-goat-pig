import React from 'react';
import { test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ScorecardPhotoZoom from '../ScorecardPhotoZoom';

test('renders the photo with zoom + close controls', () => {
  render(<ScorecardPhotoZoom src="blob:abc" onClose={() => {}} />);
  expect(screen.getByAltText('scorecard').getAttribute('src')).toBe('blob:abc');
  expect(screen.getByRole('button', { name: /zoom in/i })).toBeTruthy();
  expect(screen.getByRole('button', { name: /zoom out/i })).toBeTruthy();
});

test('zoom in increases the image scale', () => {
  render(<ScorecardPhotoZoom src="blob:abc" onClose={() => {}} />);
  const img = screen.getByAltText('scorecard');
  const before = img.style.width;
  fireEvent.click(screen.getByRole('button', { name: /zoom in/i }));
  expect(img.style.width).not.toBe(before);
});

test('embedded photo stays in the page and resets zoom and pan', () => {
  render(<ScorecardPhotoZoom src="blob:abc" embedded />);
  expect(screen.queryByRole('dialog')).toBeNull();
  expect(screen.queryByRole('button', { name: /close photo/i })).toBeNull();
  const img = screen.getByAltText('scorecard');
  fireEvent.click(screen.getByRole('button', { name: /zoom in/i }));
  fireEvent.click(screen.getByRole('button', { name: /reset photo/i }));
  expect(img.style.width).toBe('100%');
  expect(screen.getByRole('region', { name: /pan scorecard/i }).scrollLeft).toBe(0);
});

test('close button calls onClose', () => {
  const onClose = vi.fn();
  render(<ScorecardPhotoZoom src="blob:abc" onClose={onClose} />);
  fireEvent.click(screen.getByRole('button', { name: /close photo/i }));
  expect(onClose).toHaveBeenCalledTimes(1);
});
