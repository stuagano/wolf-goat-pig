// Tests for the tee-sheet signup safety UI (issue #323).
//
// The "Sign Me Up" button must NOT post directly to the live sheet — it first
// shows an explicit confirmation naming the player + date, and a LIVE / PREVIEW
// badge. Non-production sends dry_run so the live sheet is never mutated.
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ThemeProvider } from "../../../theme/Provider";
import WgpSignupSheet from "../WgpSignupSheet";

vi.mock("@auth0/auth0-react", () => ({
  useAuth0: vi.fn(),
}));

import { useAuth0 as mockUseAuth0 } from "@auth0/auth0-react";

// Mutable production flag so a single suite can exercise LIVE and PREVIEW.
let mockIsProduction = true;
vi.mock("../../../config/api.config", () => ({
  apiConfig: {
    baseUrl: "http://test-api.com",
    get isProduction() {
      return mockIsProduction;
    },
    get isDevelopment() {
      return !mockIsProduction;
    },
  },
  default: { baseUrl: "http://test-api.com" },
}));

const MY_NAME = "Stuart Gano";

const okJson = (body) =>
  Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(body) });

/**
 * @param {object} opts
 * @param {object} opts.signupResponse  body returned by POST /tee-sheet/signup
 * @param {function} [opts.onSignupPost] called with the parsed POST body
 */
function installFetch({ signupResponse, onSignupPost } = {}) {
  global.fetch.mockImplementation((url, opts = {}) => {
    if (url.includes("/tee-sheet/signup") && opts.method === "POST") {
      if (onSignupPost) onSignupPost(JSON.parse(opts.body));
      return okJson(
        signupResponse || { success: true, live_write: true, dry_run: false },
      );
    }
    if (url.includes("/tee-sheet/upcoming")) {
      return okJson([]);
    }
    if (url.includes("/tee-sheet?date=")) {
      return okJson({ slots: [], signed_up_count: 0 });
    }
    if (url.endsWith("/players/me")) {
      return okJson({ id: 7, name: "Auth0 Name", legacy_name: MY_NAME });
    }
    return okJson({});
  });
}

const renderSheet = () =>
  render(
    <ThemeProvider>
      <WgpSignupSheet />
    </ThemeProvider>,
  );

beforeEach(() => {
  mockIsProduction = true;
  mockUseAuth0.mockReturnValue({
    isAuthenticated: true,
    getAccessTokenSilently: vi.fn().mockResolvedValue("token-123"),
  });
});

describe("WgpSignupSheet — LIVE (production)", () => {
  test("shows a LIVE badge and requires confirmation before posting", async () => {
    const posts = [];
    installFetch({ onSignupPost: (b) => posts.push(b) });
    renderSheet();

    // LIVE badge visible.
    const badge = await screen.findByTestId("signup-env-badge");
    expect(badge).toHaveTextContent(/LIVE/i);

    // Click "Sign Me Up" — this must NOT post yet, only reveal a confirmation.
    fireEvent.click(await screen.findByRole("button", { name: "Sign Me Up" }));

    const confirmBox = await screen.findByTestId("signup-confirm");
    expect(confirmBox).toHaveTextContent(MY_NAME);
    expect(confirmBox).toHaveTextContent(/LIVE/);

    // No POST happened just from clicking "Sign Me Up".
    expect(posts).toHaveLength(0);
  });

  test("confirming posts with dry_run:false and shows the signed-up message", async () => {
    const posts = [];
    installFetch({ onSignupPost: (b) => posts.push(b) });
    renderSheet();

    fireEvent.click(await screen.findByRole("button", { name: "Sign Me Up" }));
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Yes, sign me up on the LIVE sheet/i,
      }),
    );

    await waitFor(() => {
      expect(posts).toHaveLength(1);
    });
    expect(posts[0]).toEqual({
      date: expect.any(String),
      name: MY_NAME,
      dry_run: false,
    });

    expect(await screen.findByText(/You're signed up as/i)).toBeInTheDocument();
  });

  test("Cancel dismisses the confirmation without posting", async () => {
    const posts = [];
    installFetch({ onSignupPost: (b) => posts.push(b) });
    renderSheet();

    fireEvent.click(await screen.findByRole("button", { name: "Sign Me Up" }));
    await screen.findByTestId("signup-confirm");
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    await waitFor(() => {
      expect(screen.queryByTestId("signup-confirm")).not.toBeInTheDocument();
    });
    expect(posts).toHaveLength(0);
    // Back to the initial button.
    expect(screen.getByRole("button", { name: "Sign Me Up" })).toBeInTheDocument();
  });
});

describe("WgpSignupSheet — PREVIEW (non-production)", () => {
  beforeEach(() => {
    mockIsProduction = false;
  });

  test("shows a Preview badge and sends dry_run:true, surfacing the preview result", async () => {
    const posts = [];
    installFetch({
      signupResponse: {
        success: true,
        live_write: false,
        dry_run: true,
        would_sign_up: { name: MY_NAME, date: "2099-01-04" },
      },
      onSignupPost: (b) => posts.push(b),
    });
    renderSheet();

    const badge = await screen.findByTestId("signup-env-badge");
    expect(badge).toHaveTextContent(/Preview/i);

    fireEvent.click(await screen.findByRole("button", { name: "Sign Me Up" }));
    const confirmBox = await screen.findByTestId("signup-confirm");
    expect(confirmBox).toHaveTextContent(/Preview mode/i);

    fireEvent.click(screen.getByRole("button", { name: /Yes, preview it/i }));

    await waitFor(() => {
      expect(posts).toHaveLength(1);
    });
    expect(posts[0].dry_run).toBe(true);

    // Result message makes clear the live sheet was not changed.
    expect(
      await screen.findByText(/LIVE tee sheet was not changed/i),
    ).toBeInTheDocument();
  });
});
