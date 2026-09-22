import { describe, expect, it } from "vitest";

import { CARD_DEFINITIONS } from "../src/cards/definitions";
import { normalizeConfig, stubConfig } from "../src/utilities/config";

describe("card configuration", () => {
  it("provides a complete picker default for every card", () => {
    expect(CARD_DEFINITIONS).toHaveLength(11);
    for (const definition of CARD_DEFINITIONS) {
      const config = stubConfig(definition);
      expect(config.type).toBe(`custom:${definition.tag}`);
      expect(config.metrics).toEqual(definition.defaultMetrics);
      expect(config.layout).toBe(definition.defaultLayout);
      expect(config.repositories).toBe("auto");
    }
  });

  it("normalizes configuration without mutating user arrays", () => {
    const definition = CARD_DEFINITIONS[1];
    const metrics = ["actions_runtime"];
    const config = normalizeConfig(
      {
        type: `custom:${definition.tag}`,
        metrics,
        severity: { amber: 65, red: 85 },
      },
      definition,
    );
    metrics.push("actions_cost");

    expect(config.metrics).toEqual(["actions_runtime"]);
    expect(config.severity).toEqual({ green: 0, amber: 65, red: 85 });
  });

  it("copies and sanitizes repository display overrides", () => {
    const definition = CARD_DEFINITIONS.find((card) => card.kind === "repositories")!;
    const metrics = ["stars"];
    const config = normalizeConfig(
      {
        type: `custom:${definition.tag}`,
        repository_overrides: {
          "octo/repo": {
            title: "Important",
            view: "expanded",
            favorite: true,
            metrics,
            metric_badges: [{ attribute: "visibility", label: "Access" }],
          },
        },
      },
      definition,
    );
    metrics.push("forks");

    expect(config.repository_overrides?.["octo/repo"]).toEqual({
      title: "Important",
      view: "expanded",
      favorite: true,
      metrics: ["stars"],
      metric_badges: [
        { attribute: "visibility", icon: undefined, label: "Access" },
      ],
    });
  });

  it("rejects a mismatched card type", () => {
    expect(() =>
      normalizeConfig(
        { type: "custom:not-github-insights" },
        CARD_DEFINITIONS[0],
      ),
    ).toThrow("Expected type");
  });

  it("normalizes the legacy show_forks option into repository exclusion", () => {
    const definition = CARD_DEFINITIONS.find((card) => card.kind === "repositories")!;

    expect(
      normalizeConfig(
        {
          type: `custom:${definition.tag}`,
          show_forks: false,
        },
        definition,
      ).exclude?.forked,
    ).toBe(true);
    expect(
      normalizeConfig(
        {
          type: `custom:${definition.tag}`,
          show_forks: false,
          exclude: { forked: false },
        },
        definition,
      ).exclude?.forked,
    ).toBe(false);
  });

  it("keeps billing concepts as distinct metric keys", () => {
    const usage = CARD_DEFINITIONS.find((card) => card.kind === "usage");
    expect(usage?.defaultMetrics).toEqual(
      expect.arrayContaining([
        "actions_discounted_usage",
        "actions_billable_usage",
        "actions_cost",
        "actions_budget",
        "actions_estimated_minutes_remaining",
      ]),
    );
  });

  it("snapshots registered card metadata", () => {
    expect(
      CARD_DEFINITIONS.map(({ kind, tag, editorTag }) => ({
        kind,
        tag,
        editorTag,
      })),
    ).toMatchSnapshot();
  });
});
