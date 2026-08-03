// frontend/src/components/admin/__tests__/RosterManager.test.jsx
import React from "react";
import { render, screen, waitFor, fireEvent, within } from "@testing-library/react";
import RosterManager from "../RosterManager";

const ADMIN_EMAIL = "stuagano@gmail.com";
const ACCESS_TOKEN = "admin-access-token";
const API_URL = "http://test-api.com"; // matches VITE_API_URL stub in setupTests

const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

// Mutable auth identity so individual tests can switch admin/non-admin.
let mockAuth = {
  user: { sub: "auth0|admin", email: ADMIN_EMAIL },
  isAuthenticated: true,
  isLoading: false,
  getAccessTokenSilently: vi.fn().mockResolvedValue(ACCESS_TOKEN),
};
vi.mock("@auth0/auth0-react", () => ({
  useAuth0: () => mockAuth,
}));

const PENDING = [
  { id: 11, name: "Alice Adams", email: "alice@example.com", status: "pending" },
  { id: 22, name: "Bob Brown", email: null, status: "pending" },
];

const okJson = (body) =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(""),
  });

function installAdminFetch(pending = PENDING) {
  global.fetch.mockImplementation((url, opts = {}) => {
    if (url.endsWith("/players/me")) {
      return okJson({
        id: 1,
        name: "Admin",
        role: "super_admin",
        is_super_admin: true,
      });
    }
    if (url.includes("/legacy-players/pending") && !url.includes("/promote") && !url.includes("/dismiss")) {
      return okJson({ count: pending.length, status: "pending", players: pending });
    }
    if (url.includes("/promote")) {
      return okJson({
        promoted: true,
        canonical_name: "Alice Adams",
        profile_linked: true,
        profile_link_status: "linked",
      });
    }
    if (url.includes("/dismiss")) {
      return okJson({ dismissed: true, name: "Bob Brown" });
    }
    if (url.endsWith("/legacy-players") && opts.method === "POST") {
      return okJson({ added: true, canonical_name: "Jane Smith", message: "Added" });
    }
    return okJson({});
  });
}

/** Find the fetch call whose URL matches a predicate. */
function findCall(predicate) {
  return global.fetch.mock.calls.find(([url, opts]) => predicate(url, opts));
}

beforeEach(() => {
  mockAuth = {
    user: { sub: "auth0|admin", email: ADMIN_EMAIL },
    isAuthenticated: true,
    isLoading: false,
    getAccessTokenSilently: vi.fn().mockResolvedValue(ACCESS_TOKEN),
  };
  mockNavigate.mockClear();
  installAdminFetch();
});

describe("RosterManager", () => {
  test("renders a row for each pending player", async () => {
    render(<RosterManager />);
    expect(await screen.findByTestId("pending-row-11")).toBeInTheDocument();
    expect(screen.getByTestId("pending-row-22")).toBeInTheDocument();
    expect(screen.getByText("Alice Adams")).toBeInTheDocument();
    expect(screen.getByText("Bob Brown")).toBeInTheDocument();
    expect(screen.getByText("alice@example.com")).toBeInTheDocument();

    // Pending list was fetched with a verified bearer token.
    const listCall = findCall((url) => url.includes("/legacy-players/pending?status=pending"));
    expect(listCall).toBeTruthy();
    expect(listCall[1].headers.Authorization).toBe(`Bearer ${ACCESS_TOKEN}`);
  });

  test("PROMOTE posts to the promote endpoint with bearer auth", async () => {
    render(<RosterManager />);
    await screen.findByTestId("pending-row-11");

    const row = screen.getByTestId("pending-row-11");
    fireEvent.click(within(row).getByText("Promote"));

    await waitFor(() => {
      const call = findCall((url) => url.endsWith("/legacy-players/pending/11/promote"));
      expect(call).toBeTruthy();
      expect(call[1].method).toBe("POST");
      expect(call[1].headers.Authorization).toBe(`Bearer ${ACCESS_TOKEN}`);
      expect(call[1].headers["Content-Type"]).toBe("application/json");
    });
    // Success feedback shown.
    expect(await screen.findByTestId("roster-feedback")).toHaveTextContent(
      /Promoted.*linked the player's account/i,
    );
    // List must be re-fetched after promote (refresh-after-mutation).
    await waitFor(() => {
      const refreshCalls = global.fetch.mock.calls.filter(
        ([url]) => url.includes("/legacy-players/pending?status=pending"),
      );
      expect(refreshCalls.length).toBeGreaterThanOrEqual(2);
    });
  });

  test("DISMISS posts to the dismiss endpoint with bearer auth", async () => {
    render(<RosterManager />);
    await screen.findByTestId("pending-row-22");

    const row = screen.getByTestId("pending-row-22");
    fireEvent.click(within(row).getByText("Dismiss"));

    await waitFor(() => {
      const call = findCall((url) => url.endsWith("/legacy-players/pending/22/dismiss"));
      expect(call).toBeTruthy();
      expect(call[1].method).toBe("POST");
      expect(call[1].headers.Authorization).toBe(`Bearer ${ACCESS_TOKEN}`);
      expect(call[1].headers["Content-Type"]).toBe("application/json");
    });
    expect(await screen.findByTestId("roster-feedback")).toHaveTextContent(/Dismissed/i);
    // List must be re-fetched after dismiss (refresh-after-mutation).
    await waitFor(() => {
      const refreshCalls = global.fetch.mock.calls.filter(
        ([url]) => url.includes("/legacy-players/pending?status=pending"),
      );
      expect(refreshCalls.length).toBeGreaterThanOrEqual(2);
    });
  });

  test("ADD form POSTs the new name to the canonical roster", async () => {
    render(<RosterManager />);
    await screen.findByTestId("pending-row-11");

    fireEvent.change(screen.getByLabelText("Player full name"), {
      target: { value: "Jane Smith" },
    });
    fireEvent.click(screen.getByText("Add Player"));

    await waitFor(() => {
      const call = findCall(
        (url, opts) => url.endsWith("/legacy-players") && opts?.method === "POST",
      );
      expect(call).toBeTruthy();
      expect(JSON.parse(call[1].body)).toEqual({ name: "Jane Smith" });
      expect(call[1].headers.Authorization).toBe(`Bearer ${ACCESS_TOKEN}`);
      expect(call[1].headers["Content-Type"]).toBe("application/json");
    });
    expect(await screen.findByTestId("roster-feedback")).toHaveTextContent(/Added/i);
  });

  test("shows the empty state when there are no pending players", async () => {
    installAdminFetch([]);
    render(<RosterManager />);
    expect(await screen.findByTestId("pending-empty")).toBeInTheDocument();
  });

  test("non-admins see Access Denied and no roster fetch is made", async () => {
    mockAuth = {
      user: { sub: "auth0|nobody", email: "random@nobody.com" },
      isAuthenticated: true,
      isLoading: false,
      getAccessTokenSilently: vi.fn().mockResolvedValue("normal-user-token"),
    };
    installServerAdminFetch({ isSuperAdmin: false });

    render(<RosterManager />);
    expect(await screen.findByText("Access Denied")).toBeInTheDocument();

    expect(
      findCall((url) => url.includes("/legacy-players/pending")),
    ).toBeFalsy();
  });
});

// Server-driven role gating: /players/me is authoritative.
function installServerAdminFetch({ isSuperAdmin, pending = PENDING } = {}) {
  global.fetch.mockImplementation((url, opts = {}) => {
    if (url.endsWith("/players/me")) {
      return okJson({
        id: 1,
        name: "Someone",
        role: isSuperAdmin ? "super_admin" : "normal",
        is_super_admin: isSuperAdmin,
      });
    }
    if (url.includes("/legacy-players/pending")) {
      return okJson({ count: pending.length, status: "pending", players: pending });
    }
    if (url.endsWith("/legacy-players") && opts.method === "POST") {
      return okJson({ added: true, canonical_name: "Jane Smith" });
    }
    return okJson({});
  });
}

describe("RosterManager server-driven admin", () => {
  test("server super-admin role grants access regardless of browser email", async () => {
    mockAuth = {
      user: { sub: "auth0|nobody", email: "random@nobody.com" },
      isAuthenticated: true,
      isLoading: false,
      getAccessTokenSilently: vi.fn().mockResolvedValue("token"),
    };
    installServerAdminFetch({ isSuperAdmin: true });

    render(<RosterManager />);
    // Roster content loads because the server says this account is an admin.
    expect(await screen.findByTestId("pending-row-11")).toBeInTheDocument();
    expect(screen.queryByText("Access Denied")).not.toBeInTheDocument();
  });

  test("server normal role denies access regardless of browser email", async () => {
    mockAuth = {
      user: { sub: "auth0|admin", email: ADMIN_EMAIL },
      isAuthenticated: true,
      isLoading: false,
      getAccessTokenSilently: vi.fn().mockResolvedValue("token"),
    };
    installServerAdminFetch({ isSuperAdmin: false });

    render(<RosterManager />);
    expect(await screen.findByText("Access Denied")).toBeInTheDocument();
    expect(screen.getByTestId("denied-not-admin")).toHaveTextContent(/normal user/);
    expect(screen.queryByTestId("denied-signed-out")).not.toBeInTheDocument();
  });

  test("signed-out visitors get the 'not signed in' denial copy", async () => {
    mockAuth = { user: null, isAuthenticated: false, isLoading: false };
    render(<RosterManager />);
    expect(await screen.findByText("Access Denied")).toBeInTheDocument();
    expect(screen.getByTestId("denied-signed-out")).toBeInTheDocument();
    expect(screen.queryByTestId("denied-not-admin")).not.toBeInTheDocument();
  });
});
