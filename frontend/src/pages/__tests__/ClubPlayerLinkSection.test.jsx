// Tests for the Account page "Club Player" section, which lets a user link,
// change, or unlink their Wing Point tee-sheet name any time after onboarding.
//
// Mocks only Auth0 and fetch (same pattern as OnboardingWrapper.test.jsx),
// exercising the real usePlayerProfile hook + LegacyNameSelector underneath.
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ClubPlayerLinkSection } from "../AccountPage";

vi.mock("@auth0/auth0-react", () => ({
  useAuth0: vi.fn(),
}));

import { useAuth0 as mockUseAuth0 } from "@auth0/auth0-react";

const LEGACY_PLAYERS = ["Alice Adams", "Bob Brown", "Stuart Gano", "Jane Smith"];

const theme = {
  isDark: false,
  buttonStyle: {},
  colors: {
    primary: "#047857",
    success: "#10b981",
    error: "#ef4444",
    textPrimary: "#111",
    textSecondary: "#666",
    gray200: "#e5e7eb",
    border: "#ddd",
  },
};

const okJson = (body) =>
  Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });

function installFetch({ legacyName = null, suggestion = null, onPut } = {}) {
  global.fetch.mockImplementation((url, opts = {}) => {
    if (url.endsWith("/players/me/legacy-name") && opts.method === "PUT") {
      const body = JSON.parse(opts.body);
      if (onPut) onPut(body);
      return okJson({
        id: 7,
        name: "Auth0 Name",
        legacy_name: body.legacy_name,
        legacy_name_suggestion: null,
      });
    }
    if (url.endsWith("/players/me")) {
      return okJson({
        id: 7,
        name: "Auth0 Name",
        legacy_name: legacyName,
        legacy_name_suggestion: suggestion,
      });
    }
    if (url.endsWith("/legacy-players")) {
      return okJson({ players: LEGACY_PLAYERS });
    }
    return okJson({});
  });
}

const renderSection = () =>
  render(<ClubPlayerLinkSection cardStyle={{}} sectionTitle={{}} theme={theme} />);

beforeEach(() => {
  mockUseAuth0.mockReturnValue({
    isAuthenticated: true,
    getAccessTokenSilently: vi.fn().mockResolvedValue("token-123"),
  });
  localStorage.clear();
});

describe("ClubPlayerLinkSection", () => {
  test("shows the linked name with Change / Unlink when already linked", async () => {
    installFetch({ legacyName: "Stuart Gano" });
    renderSection();

    expect(await screen.findByText("Stuart Gano")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Change/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Unlink$/i })).toBeInTheDocument();
  });

  test("unlinked state links a chosen name via PUT", async () => {
    const putBodies = [];
    installFetch({ legacyName: null, onPut: (b) => putBodies.push(b) });
    renderSection();

    // Unlinked prompt → open the selector.
    fireEvent.click(await screen.findByRole("button", { name: /Link my club player/i }));

    const search = await screen.findByPlaceholderText(/Search for your name/i);
    fireEvent.change(search, { target: { value: "Jane" } });
    fireEvent.click(await screen.findByText("Jane Smith"));
    fireEvent.click(screen.getByRole("button", { name: /Confirm: Jane Smith/i }));

    await waitFor(() => {
      expect(putBodies).toEqual([{ legacy_name: "Jane Smith" }]);
    });
    // Returns to the linked view (Change/Unlink controls appear).
    expect(await screen.findByRole("button", { name: /Change/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Unlink$/i })).toBeInTheDocument();
  });

  test("unlink asks for confirmation then PUTs a null legacy_name", async () => {
    const putBodies = [];
    installFetch({ legacyName: "Stuart Gano", onPut: (b) => putBodies.push(b) });
    renderSection();

    fireEvent.click(await screen.findByRole("button", { name: /^Unlink$/i }));
    // Confirmation step.
    fireEvent.click(await screen.findByRole("button", { name: /Yes, unlink/i }));

    await waitFor(() => {
      expect(putBodies).toEqual([{ legacy_name: null }]);
    });
    expect(await screen.findByText(/Not linked yet/i)).toBeInTheDocument();
  });

  test("Cancel from the selector returns to the linked view without a PUT", async () => {
    installFetch({ legacyName: "Stuart Gano" });
    renderSection();

    fireEvent.click(await screen.findByRole("button", { name: /Change/i }));
    // Selector is open; back out.
    fireEvent.click(await screen.findByRole("button", { name: /^Cancel$/i }));

    expect(await screen.findByText("Stuart Gano")).toBeInTheDocument();
    const putCall = global.fetch.mock.calls.find(
      ([url, opts]) => url.endsWith("/players/me/legacy-name") && opts?.method === "PUT",
    );
    expect(putCall).toBeUndefined();
  });
});
