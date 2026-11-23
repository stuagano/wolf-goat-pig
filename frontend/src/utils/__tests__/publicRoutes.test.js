import { describe, expect, test } from 'vitest';
import { isLoginOptionalRoute } from '../publicRoutes';

describe('isLoginOptionalRoute', () => {
  test('lets a signup cancel link through the login wall', () => {
    expect(isLoginOptionalRoute('/signup/cancel/eyJ.sig')).toBe(true);
  });

  test('still requires login for the signup sheet and the bare cancel path', () => {
    expect(isLoginOptionalRoute('/signup')).toBe(false);
    expect(isLoginOptionalRoute('/signup/cancel')).toBe(false);
  });

  test('keeps the scorekeeper deep link public', () => {
    expect(isLoginOptionalRoute('/game/abc')).toBe(true);
    expect(isLoginOptionalRoute('/game')).toBe(false);
  });
});
