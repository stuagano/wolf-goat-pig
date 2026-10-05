// Tests for the fuzzy legacy-name onboarding flow (issues #322 / #321).
//
// These exercise the real usePlayerProfile hook wired through OnboardingWrapper
// → OnboardingModal → LegacyNameSelector, mocking only Auth0 and fetch (the same
// pattern DailySignupView / RosterManager tests use).
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import OnboardingWrapper from "../OnboardingWrapper";
import usePlayerProfile from "../../../hooks/usePlayerProfile";

vi.mock("@auth0/auth0-react", () => ({
  useAuth0: vi.fn(),
}));

import { useAuth0 as mockUseAuth0 } from "@auth0/auth0-react";

const SUGGESTION = "Stuart Gano";
const LEGACY_PLAYERS = ["Alice Adams", "Bob Brown", "Stuart Gano", "Jane Smith"];

const ProfileObserver = () => {
  const { profile, legacyNameSkipped } = usePlayerProfile();
  return (
    <>
      <span data-testid="skip-state">{String(legacyNameSkipped)}</span>
      <span data-testid="linked-name">{profile?.legacy_name || ""}</span>
    </>
  );
};

const okJson = (body) =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  });

/**
 * Install a fetch mock for the onboarding flow.
 * @param {object} opts
 * @param {string|null} opts.legacyName    profile.legacy_name
 * @param {string|null} opts.suggestion    profile.legacy_name_suggestion
 * @param {function} [opts.onPut]          called with the PUT body
 */
function installFetch({ legacyName = null, suggestion = SUGGESTION, onPut } = {}) {
  global.fetch.mockImplementation((url, opts = {}) => {
    if (url.endsWith("/players/me/legacy-name") && opts.method === "PUT") {
      const body = JSON.parse(opts.body);
      if (onPut) onPut(body);
      return okJson({
        legacy_name: body.legacy_name,
        legacy_name_suggestion: null,
        is_admin: false,
      });
    }
    if (url.endsWith("/players/me")) {
      return okJson({
        id: 7,
        name: "Auth0 Name",
        legacy_name: legacyName,
        legacy_name_suggestion: suggestion,
        is_admin: false,
      });
    }
    if (url.endsWith("/legacy-players")) {
      return okJson({ players: LEGACY_PLAYERS });
    }
    return okJson({});
  });
}

beforeEach(() => {
  mockUseAuth0.mockReturnValue({
    isAuthenticated: true,
    isLoading: false,
    user: { sub: "auth0|stu", name: "Auth0 Name", email: "stu@example.com" },
    getAccessTokenSilently: vi.fn().mockResolvedValue("token-123"),
  });
  localStorage.clear();
});

// Linking is now optional — needsLegacyName is permanently false.
// The modal never blocks new users regardless of profile state.
describe("OnboardingWrapper fuzzy legacy-name flow", () => {
  test("offers optional history linking and honors skip for this login", async () => {
    installFetch();
    render(<OnboardingWrapper><div>App Content</div></OnboardingWrapper>);
    expect(await screen.findByRole("button", { name: "Find my player history" })).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Not now" }));
    expect(screen.queryByRole("button", { name: "Find my player history" })).not.toBeInTheDocument();
    expect(screen.getByText("App Content")).toBeInTheDocument();
  });

  test("opens the existing selector only on request and shows an admin conflict", async () => {
    installFetch();
    const fetchNormal = global.fetch.getMockImplementation();
    global.fetch.mockImplementation((url, options) => {
      if (options?.method === "PUT") return Promise.resolve({ ok: false, status: 409, json: async () => ({ detail: "Ask a club admin to review Account links." }) });
      return fetchNormal(url, options);
    });
    render(<OnboardingWrapper><div>App Content</div></OnboardingWrapper>);
    fireEvent.click(await screen.findByRole("button", { name: "Find my player history" }));
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Yes, link this player" }));
    expect(await screen.findByText("Ask a club admin to review Account links.")).toBeInTheDocument();
  });

  test("shows the server's profile error with retry and sign-in actions", async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 403, json: async () => ({ detail: "Verify your email address, then sign in again." }) });
    render(<OnboardingWrapper><div>App Content</div></OnboardingWrapper>);
    expect(await screen.findByRole("alert")).toHaveTextContent("Verify your email address");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in again" })).toBeInTheDocument();
  });

  test("never shows the onboarding modal even when legacy_name is null", async () => {
    installFetch({ legacyName: null, suggestion: SUGGESTION });

    render(
      <OnboardingWrapper>
        <div>App Content</div>
      </OnboardingWrapper>,
    );

    expect(await screen.findByText("App Content")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText(/Link Your Account/i)).not.toBeInTheDocument();
    });
  });

  test("does not show the modal when legacy_name is already set", async () => {
    installFetch({ legacyName: "Stuart Gano", suggestion: null });

    render(
      <OnboardingWrapper>
        <div>App Content</div>
      </OnboardingWrapper>,
    );

    expect(await screen.findByText("App Content")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText(/Link Your Account/i)).not.toBeInTheDocument();
    });
  });

  test("does not show the modal even when another account has skipped", async () => {
    localStorage.setItem("legacy_name_skipped:auth0|someone-else", "true");
    installFetch({ legacyName: null, suggestion: SUGGESTION });

    render(
      <OnboardingWrapper>
        <div>App Content</div>
      </OnboardingWrapper>,
    );

    expect(await screen.findByText("App Content")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText(/Link Your Account/i)).not.toBeInTheDocument();
    });
  });
});
