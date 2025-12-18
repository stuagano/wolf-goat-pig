// frontend/src/hooks/__tests__/useAuth.test.js
import { renderHook } from '@testing-library/react';
import { useAuth } from '../useAuth';
import { useAuth0 } from '@auth0/auth0-react';
import { createMockAuthContext, createMockUser } from '../../test-utils/mockFactories';

// Mock the auth0 hook
jest.mock('@auth0/auth0-react');

describe('useAuth', () => {
  const mockAuth0Return = {
    ...createMockAuthContext(),
    getAccessTokenSilently: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    useAuth0.mockReturnValue(mockAuth0Return);
  });

  describe('isLoggedIn', () => {
    test('should return false when not authenticated', () => {
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        isAuthenticated: false,
        isLoading: false,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.isLoggedIn).toBe(false);
    });

    test('should return false when authenticated but still loading', () => {
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        isAuthenticated: true,
        isLoading: true,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.isLoggedIn).toBe(false);
    });

    test('should return true when authenticated and not loading', () => {
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        isAuthenticated: true,
        isLoading: false,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.isLoggedIn).toBe(true);
    });
  });

  describe('userName', () => {
    test('should return "Player" when user is null', () => {
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        user: null,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.userName).toBe('Player');
    });

    test('should return user name when available', () => {
      const mockUser = createMockUser({ name: 'John Doe', email: 'john@example.com' });
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        user: mockUser,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.userName).toBe('John Doe');
    });

    test('should return email when name is not available', () => {
      const mockUser = createMockUser({ name: undefined, email: 'john@example.com' });
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        user: mockUser,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.userName).toBe('john@example.com');
    });

    test('should return "Player" when neither name nor email is available', () => {
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        user: {},
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.userName).toBe('Player');
    });
  });

  describe('userEmail', () => {
    test('should return undefined when user is null', () => {
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        user: null,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.userEmail).toBeUndefined();
    });

    test('should return email when available', () => {
      const mockUser = createMockUser({ email: 'john@example.com' });
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        user: mockUser,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.userEmail).toBe('john@example.com');
    });
  });

  describe('userPicture', () => {
    test('should return undefined when user is null', () => {
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        user: null,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.userPicture).toBeUndefined();
    });

    test('should return picture URL when available', () => {
      const pictureUrl = 'https://example.com/avatar.jpg';
      const mockUser = createMockUser({ avatar_url: pictureUrl });
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        user: {
          picture: pictureUrl,
        },
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.userPicture).toBe(pictureUrl);
    });
  });

  describe('passthrough Auth0 properties', () => {
    test('should expose isAuthenticated from Auth0', () => {
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        isAuthenticated: true,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.isAuthenticated).toBe(true);
    });

    test('should expose isLoading from Auth0', () => {
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        isLoading: true,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.isLoading).toBe(true);
    });

    test('should expose loginWithRedirect from Auth0', () => {
      const loginFn = jest.fn();
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        loginWithRedirect: loginFn,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.loginWithRedirect).toBe(loginFn);
    });

    test('should expose logout from Auth0', () => {
      const logoutFn = jest.fn();
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        logout: logoutFn,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.logout).toBe(logoutFn);
    });

    test('should expose getAccessTokenSilently from Auth0', () => {
      const getTokenFn = jest.fn();
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        getAccessTokenSilently: getTokenFn,
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.getAccessTokenSilently).toBe(getTokenFn);
    });
  });

  describe('full user profile scenario', () => {
    test('should handle complete user profile', () => {
      const mockUser = createMockUser({
        name: 'John Doe',
        email: 'john@example.com',
        id: 'auth0|123456',
      });
      useAuth0.mockReturnValue({
        ...mockAuth0Return,
        isAuthenticated: true,
        isLoading: false,
        user: {
          ...mockUser,
          picture: 'https://example.com/john.jpg',
          sub: 'auth0|123456',
        },
      });

      const { result } = renderHook(() => useAuth());

      expect(result.current.isLoggedIn).toBe(true);
      expect(result.current.userName).toBe('John Doe');
      expect(result.current.userEmail).toBe('john@example.com');
      expect(result.current.userPicture).toBe('https://example.com/john.jpg');
      expect(result.current.user.sub).toBe('auth0|123456');
    });
  });
});
