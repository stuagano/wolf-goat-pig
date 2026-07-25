// Tests for the fuzzy legacy-name onboarding flow (issues #322 / #321).
//
// These exercise the real usePlayerProfile hook wired through OnboardingWrapper
// → OnboardingModal → LegacyNameSelector, mocking only Auth0 and fetch (the same
// pattern DailySignupView / RosterManager tests use).
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import OnboardingWrapper from "../OnboardingWrapper";

vi.mock("@auth0/auth0-react", () => ({
  useAuth0: vi.fn(),
}));

import { useAuth0 as mockUseAuth0 } from "@auth0/auth0-react";

const SUGGESTION = "Stuart Gano";
const LEGACY_PLAYERS = ["Alice Adams", "Bob Brown", "Stuart Gano", "Jane Smith"];

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
    user: { name: "Auth0 Name", email: "stu@example.com" },
    getAccessTokenSilently: vi.fn().mockResolvedValue("token-123"),
  });
  localStorage.clear();
});

describe("OnboardingWrapper fuzzy legacy-name flow", () => {
  test("shows the fuzzy suggestion when legacy_name_suggestion is set and legacy_name is null", async () => {
    installFetch({ legacyName: null, suggestion: SUGGESTION });

    render(
      <OnboardingWrapper>
        <div>App Content</div>
      </OnboardingWrapper>,
    );

    // Children still render underneath the modal overlay.
    expect(screen.getByText("App Content")).toBeInTheDocument();

    // "Did you mean <suggestion>?" banner appears with the suggested name.
    expect(await screen.findByText(/Did you mean/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: SUGGESTION })).toBeInTheDocument();
  });

  test("does not show the modal when the account already has a confirmed legacy_name", async () => {
    installFetch({ legacyName: "Stuart Gano", suggestion: null });

    render(
      <OnboardingWrapper>
        <div>App Content</div>
      </OnboardingWrapper>,
    );

    expect(await screen.findByText("App Content")).toBeInTheDocument();
    // No onboarding modal when the user is already linked.
    await waitFor(() => {
      expect(screen.queryByText(/Link Your Account/i)).not.toBeInTheDocument();
    });
  });

  test("selecting a name from the dropdown PUTs it and persists (modal closes)", async () => {
    const putBodies = [];
    installFetch({ legacyName: null, suggestion: SUGGESTION, onPut: (b) => putBodies.push(b) });

    render(
      <OnboardingWrapper>
        <div>App Content</div>
      </OnboardingWrapper>,
    );

    // Wait for the selector to load its player list.
    const search = await screen.findByPlaceholderText(/Search for your name/i);
    fireEvent.change(search, { target: { value: "Jane" } });

    // Pick "Jane Smith" from the dropdown.
    fireEvent.click(await screen.findByText("Jane Smith"));

    // Confirm the selection.
    fireEvent.click(screen.getByRole("button", { name: /Confirm: Jane Smith/i }));

    await waitFor(() => {
      expect(putBodies).toEqual([{ legacy_name: "Jane Smith" }]);
    });

    // After a successful link the onboarding modal closes.
    await waitFor(() => {
      expect(screen.queryByText(/Link Your Account/i)).not.toBeInTheDocument();
    });
  });

  test("clicking the suggestion button and confirming PUTs the suggested name", async () => {
    const putBodies = [];
    installFetch({ legacyName: null, suggestion: SUGGESTION, onPut: (b) => putBodies.push(b) });

    render(
      <OnboardingWrapper>
        <div>App Content</div>
      </OnboardingWrapper>,
    );

    fireEvent.click(await screen.findByRole("button", { name: SUGGESTION }));
    fireEvent.click(screen.getByRole("button", { name: new RegExp(`Confirm: ${SUGGESTION}`, "i") }));

    await waitFor(() => {
      expect(putBodies).toEqual([{ legacy_name: SUGGESTION }]);
    });
  });

  test("'Skip for now' sets the localStorage skip flag and never writes legacy_name", async () => {
    installFetch({ legacyName: null, suggestion: SUGGESTION });

    render(
      <OnboardingWrapper>
        <div>App Content</div>
      </OnboardingWrapper>,
    );

    // The main skip control in the selector.
    const skip = await screen.findByRole("button", { name: /I'm not in the list/i });
    fireEvent.click(skip);

    // Skip persists a local flag only.
    await waitFor(() => {
      expect(localStorage.setItem).toHaveBeenCalledWith("legacy_name_skipped", "true");
    });

    // No PUT to legacy-name — the account stays unlinked.
    const putCall = global.fetch.mock.calls.find(
      ([url, opts]) => url.endsWith("/players/me/legacy-name") && opts?.method === "PUT",
    );
    expect(putCall).toBeUndefined();

    // Modal closes after skipping.
    await waitFor(() => {
      expect(screen.queryByText(/Link Your Account/i)).not.toBeInTheDocument();
    });
  });
});
