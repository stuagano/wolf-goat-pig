// frontend/src/components/admin/__tests__/RosterManager.test.jsx
import React from "react";
import { render, screen, waitFor, fireEvent, within } from "@testing-library/react";
import RosterManager from "../RosterManager";

const ADMIN_EMAIL = "stuagano@gmail.com";
const API_URL = "http://test-api.com"; // matches VITE_API_URL stub in setupTests

const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

// Mutable auth identity so individual tests can switch admin/non-admin.
let mockAuth = { user: { email: ADMIN_EMAIL }, isLoading: false };
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
    if (url.endsWith("/legacy-players/pending")) {
      return okJson({ count: pending.length, status: "pending", players: pending });
    }
    if (url.includes("/promote")) {
      return okJson({ promoted: true, canonical_name: "Alice Adams" });
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
  mockAuth = { user: { email: ADMIN_EMAIL }, isLoading: false };
  mockNavigate.mockClear();
  // adminHeaders() reads localStorage 'userEmail' for the X-Admin-Email header.
  localStorage.setItem("userEmail", ADMIN_EMAIL);
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

    // Pending list was fetched with the admin auth header.
    const listCall = findCall((url) => url.endsWith("/legacy-players/pending"));
    expect(listCall).toBeTruthy();
    expect(listCall[1].headers["X-Admin-Email"]).toBe(ADMIN_EMAIL);
  });

  test("PROMOTE posts to the promote endpoint with the admin header", async () => {
    render(<RosterManager />);
    await screen.findByTestId("pending-row-11");

    const row = screen.getByTestId("pending-row-11");
    fireEvent.click(within(row).getByText("Promote"));

    await waitFor(() => {
      const call = findCall((url) => url.endsWith("/legacy-players/pending/11/promote"));
      expect(call).toBeTruthy();
      expect(call[1].method).toBe("POST");
      expect(call[1].headers["X-Admin-Email"]).toBe(ADMIN_EMAIL);
    });
    // Success feedback shown + list refreshed.
    expect(await screen.findByTestId("roster-feedback")).toHaveTextContent(/Promoted/i);
  });

  test("DISMISS posts to the dismiss endpoint with the admin header", async () => {
    render(<RosterManager />);
    await screen.findByTestId("pending-row-22");

    const row = screen.getByTestId("pending-row-22");
    fireEvent.click(within(row).getByText("Dismiss"));

    await waitFor(() => {
      const call = findCall((url) => url.endsWith("/legacy-players/pending/22/dismiss"));
      expect(call).toBeTruthy();
      expect(call[1].method).toBe("POST");
      expect(call[1].headers["X-Admin-Email"]).toBe(ADMIN_EMAIL);
    });
    expect(await screen.findByTestId("roster-feedback")).toHaveTextContent(/Dismissed/i);
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
      expect(call[1].headers["X-Admin-Email"]).toBe(ADMIN_EMAIL);
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
    mockAuth = { user: { email: "random@nobody.com" }, isLoading: false };
    localStorage.setItem("userEmail", "random@nobody.com");

    render(<RosterManager />);
    expect(await screen.findByText("Access Denied")).toBeInTheDocument();

    expect(
      findCall((url) => url.endsWith("/legacy-players/pending")),
    ).toBeFalsy();
  });
});
