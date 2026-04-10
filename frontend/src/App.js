import React, { useState, useEffect, Suspense } from "react";
import {
  Routes,
  Route,
  useNavigate,
  Navigate,
  useLocation,
} from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import ColdStartHandler from "./components/ui/ColdStartHandler";
import ErrorBoundary from "./components/ui/ErrorBoundary";
import Leaderboard from "./components/game/Leaderboard";
import { ThemeProvider, useTheme } from "./theme/Provider";
import { SheetSyncProvider } from "./context";
import { AuthProvider } from "./context/AuthContext";
import { TutorialProvider } from "./context/TutorialContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import LoginButton from "./components/auth/LoginButton";
import { OnboardingWrapper } from "./components/auth";
import { HomePage, GameScorerPage, SimpleScorekeeperPage } from "./pages";
import Navigation from "./components/ui/Navigation";
import AppFooter from "./components/ui/AppFooter";
import { BadgeNotificationManager } from "./components/game/BadgeNotification";
import UpdateNotification from "./components/ui/UpdateNotification";
import OfflineIndicator from "./components/ui/OfflineIndicator";
import { initCacheManager } from "./services/cacheManager";
import syncManager from "./services/syncManager";
import "./styles/mobile-touch.css"; // Import mobile touch optimization styles

// Lazy-loaded routes — reduces initial bundle by ~40-60%
const ShotRangeAnalyzer = React.lazy(() => import("./components/game/ShotRangeAnalyzer"));
const TutorialSystem = React.lazy(() => import("./components/tutorial/TutorialSystem"));
const WGPAnalyticsDashboard = React.lazy(() => import("./components/analytics/WGPAnalyticsDashboard"));
const SheetIntegrationDashboard = React.lazy(() => import("./components/integration/SheetIntegrationDashboard"));
const GoogleSheetsLiveSync = React.lazy(() => import("./components/integration/GoogleSheetsLiveSync"));
const SignupPage = React.lazy(() => import("./pages/SignupPage"));
const AboutPage = React.lazy(() => import("./pages/AboutPage"));
const RulesPage = React.lazy(() => import("./pages/RulesPage"));
const AdminPage = React.lazy(() => import("./pages/AdminPage"));
const DatabaseMigrations = React.lazy(() => import("./components/admin/DatabaseMigrations"));
const CreateGamePage = React.lazy(() => import("./pages/CreateGamePage"));
const JoinGamePage = React.lazy(() => import("./pages/JoinGamePage"));
const GameLobbyPage = React.lazy(() => import("./pages/GameLobbyPage"));
const ActiveGamesPage = React.lazy(() => import("./pages/ActiveGamesPage"));
const CompletedGamesPage = React.lazy(() => import("./pages/CompletedGamesPage"));
const AccountPage = React.lazy(() => import("./pages/AccountPage"));
const BadgesPage = React.lazy(() => import("./pages/BadgesPage"));
const ScorecardScanPage = React.lazy(() => import("./pages/ScorecardScanPage"));
const AskPage = React.lazy(() => import("./pages/AskPage"));

const API_URL = process.env.REACT_APP_API_URL || "";

function App() {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth0();

  const [backendReady, setBackendReady] = useState(false);
  const [showSplash, setShowSplash] = useState(true);

  // Initialize cache manager and auto-sync on app start
  useEffect(() => {
    initCacheManager();

    // Setup syncManager's auto-sync for game data
    // This handles offline queue processing when connection is restored
    const cleanupAutoSync = syncManager.setupAutoSync();

    return () => {
      cleanupAutoSync();
    };
  }, []);

  const handleBackendReady = () => {
    setBackendReady(true);
    // Load rules once backend is ready with proper error handling
    fetch(`${API_URL}/rules`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then(() => {
        // Rules loaded successfully
      })
      .catch((err) => {
        // Log error but don't block app - rules are optional
        console.warn("[App] Could not load rules:", err.message);
      });
  };

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <ThemeProvider>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            background: theme.colors.background,
          }}
        >
          <div
            style={{
              ...theme.cardStyle,
              textAlign: "center",
              padding: "40px",
            }}
          >
            <div
              style={{
                fontSize: "24px",
                marginBottom: "16px",
                color: theme.colors.primary,
              }}
            >
              🔄 Loading...
            </div>
            <p style={{ color: theme.colors.textSecondary }}>
              Checking authentication status
            </p>
          </div>
        </div>
      </ThemeProvider>
    );
  }

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return (
      <ThemeProvider>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            background: theme.colors.background,
            padding: "20px",
          }}
        >
          <div
            style={{
              ...theme.cardStyle,
              textAlign: "center",
              padding: "40px",
              maxWidth: "500px",
            }}
          >
            <div
              style={{
                fontSize: "48px",
                marginBottom: "16px",
              }}
            >
              🐷🐺🐐
            </div>
            <h1
              style={{
                color: theme.colors.primary,
                marginBottom: "8px",
                fontSize: "2.5rem",
              }}
            >
              Wolf Goat Pig
            </h1>
            <p
              style={{
                color: theme.colors.textSecondary,
                marginBottom: "24px",
                fontSize: "1.2rem",
              }}
            >
              The Ultimate Golf Betting Game
            </p>
            <p
              style={{
                color: theme.colors.textSecondary,
                marginBottom: "32px",
              }}
            >
              Please log in to start playing Wolf Goat Pig with your friends.
            </p>
            <LoginButton
              style={{
                fontSize: "18px",
                padding: "16px 32px",
                minWidth: "200px",
              }}
            />
          </div>
        </div>
      </ThemeProvider>
    );
  }

  // If backend isn't ready, show cold start handler
  if (!backendReady) {
    return (
      <ThemeProvider>
        <ColdStartHandler onReady={handleBackendReady}>
          {/* This content will show once backend is ready */}
        </ColdStartHandler>
      </ThemeProvider>
    );
  }

  // Show splash screen only on homepage after backend is ready
  if (showSplash && location.pathname === "/") {
    return (
      <ThemeProvider>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            background: theme.colors.background,
          }}
        >
          <div
            style={{
              ...theme.cardStyle,
              textAlign: "center",
              maxWidth: 400,
              marginTop: -80,
            }}
          >
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>🐷🐺🐐</div>
            <h1
              style={{
                color: theme.colors.primary,
                fontSize: 32,
                marginBottom: 16,
              }}
            >
              Wolf Goat Pig
            </h1>
            <p
              style={{
                fontSize: 18,
                color: theme.colors.textPrimary,
                marginBottom: 24,
              }}
            >
              Golf Game Tracker
            </p>
            {!isAuthenticated ? (
              <div style={{ marginBottom: "16px" }}>
                <p
                  style={{
                    fontSize: 14,
                    color: theme.colors.textSecondary,
                    marginBottom: 16,
                  }}
                >
                  Please log in to start playing
                </p>
                <LoginButton
                  style={{
                    fontSize: "18px",
                    padding: "12px 32px",
                    minWidth: "180px",
                  }}
                />
              </div>
            ) : (
              <button
                style={{
                  ...theme.buttonStyle,
                  fontSize: 22,
                  width: 220,
                  margin: "0 auto",
                }}
                onClick={() => setShowSplash(false)}
              >
                Enter Game
              </button>
            )}
            <button
              style={{
                ...theme.buttonStyle,
                fontSize: 16,
                width: 220,
                margin: "8px auto 0",
                background: "transparent",
                color: theme.colors.textSecondary,
                border: `1px solid ${theme.colors.textSecondary}`,
              }}
              onClick={() => setShowSplash(false)}
            >
              Browse Without Login
            </button>
          </div>
        </div>
      </ThemeProvider>
    );
  }

  // Main application
  return (
    <ThemeProvider>
      <OnboardingWrapper>
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Navigation />
          <OfflineIndicator />
          <BadgeNotificationManager />
          <UpdateNotification />
          <div style={{ flex: 1 }}>
            <ErrorBoundary>
            <Suspense fallback={<div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>Loading...</div>}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/game" element={<CreateGamePage />} />
              <Route path="/game/:gameId" element={<SimpleScorekeeperPage />} />
              <Route path="/game-scorer" element={<GameScorerPage />} />
              <Route
                path="/analytics"
                element={
                  <ProtectedRoute>
                    <WGPAnalyticsDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/analyzer"
                element={
                  <ProtectedRoute>
                    <ShotRangeAnalyzer />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/signup"
                element={
                  <ProtectedRoute>
                    <SignupPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route
                path="/sheets"
                element={
                  <ProtectedRoute>
                    <SheetIntegrationDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/live-sync"
                element={
                  <ProtectedRoute>
                    <GoogleSheetsLiveSync />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/tutorial"
                element={
                  <TutorialSystem
                    onComplete={() => navigate("/game")}
                    onExit={() => navigate("/")}
                  />
                }
              />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/rules" element={<RulesPage />} />
              <Route
                path="/admin"
                element={
                  <ProtectedRoute>
                    <AdminPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/migrations"
                element={
                  <ProtectedRoute>
                    <DatabaseMigrations />
                  </ProtectedRoute>
                }
              />
              <Route path="/join" element={<JoinGamePage />} />
              <Route path="/join/:code" element={<JoinGamePage />} />
              <Route path="/lobby/:gameId" element={<GameLobbyPage />} />
              <Route path="/games/active" element={<ActiveGamesPage />} />
              <Route path="/games/completed" element={<CompletedGamesPage />} />
              <Route path="/account" element={<AccountPage />} />
              <Route path="/badges" element={<BadgesPage />} />
              <Route path="/scorecard-scan" element={<ScorecardScanPage />} />
              <Route path="/ask" element={<AskPage />} />
              <Route path="/tee-times" element={<Navigate to="/signup" />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
            </Suspense>
            </ErrorBoundary>
          </div>
          <AppFooter />
        </div>
      </OnboardingWrapper>
    </ThemeProvider>
  );
}

// Main App wrapper with providers
const AppWithProviders = () => {
  return (
    <AuthProvider>
      <SheetSyncProvider>
        <TutorialProvider>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </TutorialProvider>
      </SheetSyncProvider>
    </AuthProvider>
  );
};

export default AppWithProviders;
