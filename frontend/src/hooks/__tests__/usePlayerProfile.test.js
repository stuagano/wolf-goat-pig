import { act, renderHook, waitFor } from "@testing-library/react";
import { useAuth0 } from "@auth0/auth0-react";
import usePlayerProfile from "../usePlayerProfile";

vi.mock("@auth0/auth0-react", () => ({
  useAuth0: vi.fn(),
}));

const PROFILE_UPDATED_EVENT = "wgp:player-profile-updated";
const LEGACY_SKIP_UPDATED_EVENT = "wgp:legacy-name-skip-updated";

function profileResponse(profile) {
  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(profile),
  });
}

function deferredResponse() {
  let resolve;
  const promise = new Promise((resolvePromise) => {
    resolve = (profile) => resolvePromise({
      ok: true,
      status: 200,
      json: () => Promise.resolve(profile),
    });
  });
  return { promise, resolve };
}

describe("usePlayerProfile synchronization", () => {
  const getAccessTokenSilently = vi.fn().mockResolvedValue("token");

  beforeEach(() => {
    useAuth0.mockReturnValue({
      isAuthenticated: true,
      user: { sub: "auth0|one" },
      getAccessTokenSilently,
    });
    global.fetch.mockImplementation(() => profileResponse({
      id: 1,
      legacy_name: null,
      legacy_name_suggestion: "Player One",
    }));
    localStorage.clear();
  });

  test("ignores other users' events and removes listeners on unmount", async () => {
    const removeEventListener = vi.spyOn(window, "removeEventListener");
    const { result, unmount } = renderHook(() => usePlayerProfile());

    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      window.dispatchEvent(new CustomEvent(PROFILE_UPDATED_EVENT, {
        detail: {
          userSub: "auth0|two",
          profile: { id: 2, legacy_name: "Player Two" },
        },
      }));
      window.dispatchEvent(new CustomEvent(LEGACY_SKIP_UPDATED_EVENT, {
        detail: { userSub: "auth0|two", skipped: true },
      }));
    });

    expect(result.current.profile.id).toBe(1);
    expect(result.current.legacyNameSkipped).toBe(false);

    unmount();

    expect(removeEventListener).toHaveBeenCalledWith(
      PROFILE_UPDATED_EVENT,
      expect.any(Function),
    );
    expect(removeEventListener).toHaveBeenCalledWith(
      LEGACY_SKIP_UPDATED_EVENT,
      expect.any(Function),
    );
  });

  test("does not let an earlier user's request overwrite the current user", async () => {
    const firstResponse = deferredResponse();
    const secondResponse = deferredResponse();
    global.fetch
      .mockImplementationOnce(() => firstResponse.promise)
      .mockImplementationOnce(() => secondResponse.promise);

    const { result, rerender } = renderHook(() => usePlayerProfile());
    useAuth0.mockReturnValue({
      isAuthenticated: true,
      user: { sub: "auth0|two" },
      getAccessTokenSilently,
    });
    rerender();

    await act(async () => {
      secondResponse.resolve({ id: 2, legacy_name: "Player Two" });
      await secondResponse.promise;
    });
    expect(result.current.profile.id).toBe(2);

    await act(async () => {
      firstResponse.resolve({ id: 1, legacy_name: "Player One" });
      await firstResponse.promise;
    });
    expect(result.current.profile.id).toBe(2);
  });

  test("does not let a pending fetch overwrite a synchronized profile update", async () => {
    const pendingResponse = deferredResponse();
    global.fetch.mockImplementationOnce(() => pendingResponse.promise);
    const { result } = renderHook(() => usePlayerProfile());

    act(() => {
      window.dispatchEvent(new CustomEvent(PROFILE_UPDATED_EVENT, {
        detail: {
          userSub: "auth0|one",
          profile: { id: 1, legacy_name: "Player One" },
        },
      }));
    });
    expect(result.current.profile.legacy_name).toBe("Player One");

    await act(async () => {
      pendingResponse.resolve({
        id: 1,
        legacy_name: null,
        legacy_name_suggestion: "Player One",
      });
      await pendingResponse.promise;
    });
    expect(result.current.profile.legacy_name).toBe("Player One");
  });
});
