import { describe, expect, it } from "vitest";
import { normalizeMinus } from "../PostRoundForm";

describe("normalizeMinus", () => {
  it("maps iOS/Unicode dashes to an ASCII hyphen", () => {
    expect(normalizeMinus("−3")).toBe("-3"); // minus sign
    expect(normalizeMinus("–3")).toBe("-3"); // en dash
    expect(normalizeMinus("—3")).toBe("-3"); // em dash (Smart Punctuation "--")
  });

  it("leaves plain values alone", () => {
    expect(normalizeMinus("-3")).toBe("-3");
    expect(normalizeMinus("8")).toBe("8");
    expect(normalizeMinus("")).toBe("");
  });
});
