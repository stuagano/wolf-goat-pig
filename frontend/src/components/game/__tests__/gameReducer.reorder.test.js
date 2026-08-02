import { describe, expect, test } from "vitest";
import {
  createInitialState,
  gameActions,
  gameReducer,
} from "../gameReducer";
import { nudgeHittingOrder } from "../../../utils/hittingOrder";

const players = [
  { id: "p1", name: "Alice", handicap: 10 },
  { id: "p2", name: "Bob", handicap: 12 },
  { id: "p3", name: "Carol", handicap: 8 },
  { id: "p4", name: "Dave", handicap: 15 },
];

describe("REORDER_HITTING_ORDER", () => {
  test("sets order, makes first player captain, and clears hole setup", () => {
    let state = createInitialState({ players, baseWager: 1 });

    state = gameReducer(
      state,
      gameActions.setTeam1(["p1", "p2"]),
    );
    state = gameReducer(
      state,
      gameActions.setTeam2(["p3", "p4"]),
    );
    state = gameReducer(
      state,
      gameActions.setCaptainIndex(2),
    );
    state = gameReducer(
      state,
      gameActions.setFloatInvokedBy("p1"),
    );
    state = gameReducer(
      state,
      gameActions.setOptionInvokedBy("p2"),
    );
    state = gameReducer(
      state,
      gameActions.setDuncanInvoked(true),
    );
    state = gameReducer(
      state,
      gameActions.setAardvarkRequestedTeam("team1"),
    );

    const newOrder = ["p4", "p3", "p2", "p1"];
    state = gameReducer(
      state,
      gameActions.reorderHittingOrder(newOrder),
    );

    expect(state.rotation.order).toEqual(newOrder);
    expect(state.rotation.captainIndex).toBe(0);
    expect(state.teams.team1).toEqual([]);
    expect(state.teams.team2).toEqual([]);
    expect(state.teams.captain).toBeNull();
    expect(state.teams.opponents).toEqual([]);
    expect(state.betting.floatInvokedBy).toBeNull();
    expect(state.betting.optionInvokedBy).toBeNull();
    expect(state.betting.duncanInvoked).toBe(false);
    expect(state.betting.pendingOffer).toBeNull();
    expect(state.betting.currentHoleBettingEvents).toEqual([]);
    expect(state.aardvark.requestedTeam).toBeNull();
    expect(state.aardvark.tossed).toBe(false);
  });

  test("SET_ROTATION_ORDER alone does not reset captain or teams", () => {
    let state = createInitialState({ players, baseWager: 1 });
    state = gameReducer(state, gameActions.setTeam1(["p1", "p2"]));
    state = gameReducer(state, gameActions.setCaptainIndex(1));

    const newOrder = ["p3", "p4", "p1", "p2"];
    state = gameReducer(state, gameActions.setRotationOrder(newOrder));

    expect(state.rotation.order).toEqual(newOrder);
    expect(state.rotation.captainIndex).toBe(1);
    expect(state.teams.team1).toEqual(["p1", "p2"]);
  });

  test("nudge then REORDER makes the new first player captain", () => {
    let state = createInitialState({ players, baseWager: 1 });
    state = gameReducer(state, gameActions.setCaptainIndex(0));
    state = gameReducer(state, gameActions.setTeam1(["p1", "p2"]));

    // Same path SimpleScorekeeper.movePlayerInOrder uses: nudge slot 0 down,
    // then persist via REORDER_HITTING_ORDER (first = captain).
    const nudged = nudgeHittingOrder(state.rotation.order, 0, 1);
    expect(nudged).toEqual(["p2", "p1", "p3", "p4"]);

    state = gameReducer(state, gameActions.reorderHittingOrder(nudged));
    expect(state.rotation.order).toEqual(["p2", "p1", "p3", "p4"]);
    expect(state.rotation.captainIndex).toBe(0);
    expect(state.rotation.order[0]).toBe("p2");
    expect(state.teams.team1).toEqual([]);
  });
});
