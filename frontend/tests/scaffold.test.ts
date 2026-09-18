import { describe, expect, it } from "vitest";

import { GITHUB_INSIGHTS_IMPLEMENTATION_PHASE } from "../src/index";

describe("frontend phase marker", () => {
  it("does not advertise an implemented card package", () => {
    expect(GITHUB_INSIGHTS_IMPLEMENTATION_PHASE).toBe(2);
  });
});
