import React from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { GroupPicker, MAX_OTHER_PLAYERS } from "../PostRoundForm";

const players = ["Me", "A", "B", "C", "D", "E", "F"];

const Harness = () => {
  const [selected, setSelected] = React.useState([]);
  return <GroupPicker players={players} currentName="Me" selectedNames={selected} onChange={setSelected} />;
};

it("lets you pick up to 5 others for a 6-player game, then locks the rest", () => {
  expect(MAX_OTHER_PLAYERS).toBe(5);
  render(<Harness />);
  const grid = within(screen.getByRole("group", { name: "Group members" }));
  for (const name of ["A", "B", "C", "D", "E"]) fireEvent.click(grid.getByRole("button", { name }));

  expect(grid.getByRole("button", { name: "F" })).toBeDisabled();
  expect(grid.getByRole("button", { name: "A" })).not.toBeDisabled(); // selected ones can still be removed
});
