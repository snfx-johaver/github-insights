import { describe, expect, it } from "vitest";

import {
  safeHttpUrl,
  safeHttpsUrl,
  safeText,
} from "../src/utilities/format";

describe("safe formatting helpers", () => {
  it("accepts absolute HTTP and HTTPS URLs while rejecting unsafe schemes and invalid input", () => {
    expect(safeHttpUrl("https://github.com/octo/repo")).toBe(
      "https://github.com/octo/repo",
    );
    expect(safeHttpUrl("http://github.example/octo/repo")).toBe(
      "http://github.example/octo/repo",
    );
    expect(safeHttpUrl("javascript:alert(1)")).toBeUndefined();
    expect(safeHttpUrl("/relative/path")).toBeUndefined();
    expect(safeHttpUrl(42)).toBeUndefined();
  });

  it("allows only HTTPS URLs for repository and GitHub links", () => {
    expect(safeHttpsUrl("https://github.example/octo/repo")).toBe(
      "https://github.example/octo/repo",
    );
    expect(safeHttpsUrl("http://github.example/octo/repo")).toBeUndefined();
    expect(safeHttpsUrl("data:text/html,unsafe")).toBeUndefined();
    expect(safeHttpsUrl(undefined)).toBeUndefined();
  });

  it("sanitizes primitive text, removes control characters, and enforces length limits", () => {
    expect(safeText("  public\u0000repo\n  ")).toBe("public repo");
    expect(safeText(125)).toBe("125");
    expect(safeText(true)).toBe("true");
    expect(safeText("abcdefgh", 5)).toBe("abcde");
    expect(safeText({ token: "secret" })).toBeUndefined();
    expect(safeText(" \n\t ")).toBeUndefined();
  });
});
