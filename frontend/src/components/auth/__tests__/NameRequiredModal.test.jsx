// A golfer whose sign-in only gave us their email is asked for a real name
// before the app shows the player-history prompt. Uses the real
// usePlayerProfile hook; only Auth0 and fetch are mocked.
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import OnboardingWrapper from "../OnboardingWrapper";

vi.mock("@auth0/auth0-react", () => ({
  useAuth0: vi.fn(),
}));

import { useAuth0 as mockUseAuth0 } from "@auth0/auth0-react";

const okJson = (body, status = 200) =>
  Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(body) });

function installFetch({ name = "casey@example.com", legacyName = null, pendingClaim = null, putStatus = 200 } = {}) {
  const puts = [];
  global.fetch.mockImplementation((url, opts = {}) => {
    if (url.endsWith("/players/me/name") && opts.method === "PUT") {
      const body = JSON.parse(opts.body);
      puts.push(body);
      if (putStatus !== 200) return okJson({ detail: "A player named 'Casey McFarland' already exists." }, putStatus);
      return okJson({ id: 7, name: `${body.first_name} ${body.last_name}`, legacy_name: null });
    }
    if (url.endsWith("/players/me")) {
      return okJson({ id: 7, name, legacy_name: legacyName, legacy_name_suggestion: null, pending_claim: pendingClaim });
    }
    if (url.endsWith("/legacy-players")) return okJson({ players: ["Alice Adams"] });
    return okJson({});
  });
  return puts;
}

beforeEach(() => {
  mockUseAuth0.mockReturnValue({
    isAuthenticated: true,
    isLoading: false,
    user: { sub: "auth0|casey", name: "casey@example.com", email: "casey@example.com" },
    getAccessTokenSilently: vi.fn().mockResolvedValue("token-123"),
  });
  localStorage.clear();
});

const fillName = (first, last) => {
  fireEvent.change(screen.getByLabelText("First name"), { target: { value: first } });
  fireEvent.change(screen.getByLabelText("Last name"), { target: { value: last } });
  fireEvent.click(screen.getByRole("button", { name: "Save my name" }));
};

test("asks for a name when the profile is named with an email, then saves it", async () => {
  const puts = installFetch();
  render(<OnboardingWrapper><div>app</div></OnboardingWrapper>);

  expect(await screen.findByText("What's your name?")).toBeInTheDocument();
  // The player-history banner waits until the name is set.
  expect(screen.queryByRole("region", { name: "Player history" })).not.toBeInTheDocument();

  fillName("  Casey ", "McFarland");

  await waitFor(() => expect(screen.queryByText("What's your name?")).not.toBeInTheDocument());
  expect(puts).toEqual([{ first_name: "Casey", last_name: "McFarland" }]);
  expect(screen.getByRole("region", { name: "Player history" })).toBeInTheDocument();
});

test("requires both names and rejects an email without calling the API", async () => {
  const puts = installFetch();
  render(<OnboardingWrapper><div>app</div></OnboardingWrapper>);
  await screen.findByText("What's your name?");

  fillName("Casey", " ");
  expect(screen.getByRole("alert")).toHaveTextContent("Enter your first and last name.");

  fillName("casey@example.com", "McFarland");
  expect(screen.getByRole("alert")).toHaveTextContent("can't be an email address");
  expect(puts).toEqual([]);
});

test("shows the server error and keeps asking when the name is taken", async () => {
  installFetch({ putStatus: 409 });
  render(<OnboardingWrapper><div>app</div></OnboardingWrapper>);
  await screen.findByText("What's your name?");

  fillName("Casey", "McFarland");

  expect(await screen.findByRole("alert")).toHaveTextContent("already exists");
  expect(screen.getByText("What's your name?")).toBeInTheDocument();
});

test("offers player history from the name prompt", async () => {
  installFetch();
  render(<OnboardingWrapper><div>app</div></OnboardingWrapper>);
  await screen.findByText("What's your name?");

  fireEvent.click(screen.getByRole("button", { name: "Find my player history" }));

  expect(await screen.findByRole("heading", { name: "Find my player history" })).toBeInTheDocument();
  expect(screen.queryByText("What's your name?")).not.toBeInTheDocument();
});

test.each([
  ["a real name", { name: "Casey McFarland" }],
  ["a linked club player", { legacyName: "Casey McFarland" }],
  ["a pending claim", { pendingClaim: { canonical_name: "Casey McFarland" } }],
])("does not ask for a name for %s", async (_label, opts) => {
  installFetch(opts);
  render(<OnboardingWrapper><div>app</div></OnboardingWrapper>);
  await screen.findByText("app");
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  await new Promise((resolve) => setTimeout(resolve, 0));
  expect(screen.queryByText("What's your name?")).not.toBeInTheDocument();
});
