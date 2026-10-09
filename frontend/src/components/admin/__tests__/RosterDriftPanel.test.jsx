import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import RosterDriftPanel from "../RosterDriftPanel";

const request = vi.fn();
vi.mock("../../../hooks/useAuthenticatedFetch", () => ({ useAuthenticatedFetch: () => request }));
vi.mock("../../ui", () => ({ Card: ({ children }) => <div>{children}</div> }));

const ok = data => ({ ok: true, json: async () => data });
const drift = {
  dropdown_count: 96, roster_count: 129,
  missing: ["Doug Hansen"],
  junk: [{ name: "tthiels", used_by: [] }, { name: "Grew K", used_by: [37] }],
  not_on_dropdown: ["Bob Silver"],
};

beforeEach(() => request.mockReset());

test("shows the comparison with add, remove, and in-use rows", async () => {
  request.mockResolvedValueOnce(ok(drift));
  render(<RosterDriftPanel />);
  fireEvent.click(screen.getByRole("button", { name: "Compare now" }));
  expect(await screen.findByText(/Old site: 96 names/)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Add Doug Hansen" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Remove tthiels" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Remove Grew K" })).not.toBeInTheDocument();
  expect(screen.getByText(/Used by profile #37/)).toBeInTheDocument();
  expect(screen.getByText("Bob Silver")).toBeInTheDocument();
});

test("add posts the name and refreshes", async () => {
  request.mockResolvedValueOnce(ok(drift));
  render(<RosterDriftPanel />);
  fireEvent.click(screen.getByRole("button", { name: "Compare now" }));
  request.mockResolvedValueOnce(ok({ added: true })).mockResolvedValueOnce(ok({ ...drift, missing: [] }));
  fireEvent.click(await screen.findByRole("button", { name: "Add Doug Hansen" }));
  expect(await screen.findByText("Added 'Doug Hansen' to the roster.")).toBeInTheDocument();
  expect(request.mock.calls[1][1]).toMatchObject({ method: "POST", body: JSON.stringify({ name: "Doug Hansen" }) });
});

test("remove sends DELETE with the encoded name", async () => {
  request.mockResolvedValueOnce(ok(drift));
  render(<RosterDriftPanel />);
  fireEvent.click(screen.getByRole("button", { name: "Compare now" }));
  request.mockResolvedValueOnce(ok({ removed: true })).mockResolvedValueOnce(ok(drift));
  fireEvent.click(await screen.findByRole("button", { name: "Remove tthiels" }));
  await screen.findByText("Removed 'tthiels' from the roster.");
  expect(request.mock.calls[1][0]).toMatch(/\/legacy-players\/tthiels$/);
  expect(request.mock.calls[1][1]).toEqual({ method: "DELETE" });
});

test("shows the server's error when the old site can't be read", async () => {
  request.mockResolvedValueOnce({ ok: false, status: 502, json: async () => ({ detail: "Could not read the legacy tee sheet: timeout" }) });
  render(<RosterDriftPanel />);
  fireEvent.click(screen.getByRole("button", { name: "Compare now" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Could not read the legacy tee sheet");
});
