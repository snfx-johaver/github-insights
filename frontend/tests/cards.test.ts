import { beforeAll, describe, expect, it } from "vitest";

import type {
  GitHubInsightsCardConfig,
  HomeAssistant,
} from "../src/index";
import { CARD_DEFINITIONS } from "../src/index";
import { cardStyles } from "../src/styles/card-styles";

interface TestCard extends HTMLElement {
  hass: HomeAssistant;
  setConfig(config: GitHubInsightsCardConfig): void;
  updateComplete: Promise<boolean>;
}

const entity = (
  entityId: string,
  state: string,
  attributes: Record<string, unknown> = {},
) => ({
  entity_id: entityId,
  state,
  attributes,
});

async function renderCard(
  tag: string,
  config: Partial<GitHubInsightsCardConfig>,
  states: HomeAssistant["states"],
): Promise<TestCard> {
  const card = document.createElement(tag) as TestCard;
  card.hass = { states };
  card.setConfig({
    type: `custom:${tag}`,
    ...config,
  });
  document.body.append(card);
  await card.updateComplete;
  return card;
}

describe("GitHub Insights cards", () => {
  beforeAll(() => {
    document.body.innerHTML = "";
  });

  it("registers every card and visual editor for the picker", () => {
    for (const definition of CARD_DEFINITIONS) {
      expect(customElements.get(definition.tag)).toBeDefined();
      expect(customElements.get(definition.editorTag)).toBeDefined();
    }
    expect(window.customCards).toHaveLength(11);
  });

  it("renders a useful empty state for absent capability entities", async () => {
    const card = await renderCard(
      "github-insights-copilot",
      { entities: {} },
      {},
    );
    expect(card.shadowRoot?.textContent).toContain(
      "No supported metrics are available",
    );
  });

  it("renders unavailable values and their reason", async () => {
    const card = await renderCard(
      "github-insights-security",
      {
        metrics: ["dependabot_alerts"],
        entities: { dependabot_alerts: "sensor.dependabot" },
      },
      {
        "sensor.dependabot": entity("sensor.dependabot", "unavailable", {
          availability_reason: "Missing security_events permission",
        }),
      },
    );
    expect(card.shadowRoot?.textContent).toContain("Unavailable");
    expect(card.shadowRoot?.textContent).toContain(
      "Missing security_events permission",
    );
  });

  it("visibly labels estimated equivalent minutes", async () => {
    const card = await renderCard(
      "github-insights-usage",
      {
        metrics: ["actions_estimated_minutes_remaining"],
        entities: {
          actions_estimated_minutes_remaining: "sensor.estimated_minutes",
        },
      },
      {
        "sensor.estimated_minutes": entity("sensor.estimated_minutes", "125", {
          unit_of_measurement: "min",
          source: "Estimate based on linux_standard runner",
        }),
      },
    );
    expect(card.shadowRoot?.textContent).toMatch(
      /Estimated equivalent minutes[\s\S]*Estimated/,
    );
  });

  it("can hide estimated values without hiding authoritative usage", async () => {
    const card = await renderCard(
      "github-insights-usage",
      {
        show_estimated_minutes: false,
        metrics: [
          "actions_included_usage",
          "actions_estimated_minutes_remaining",
        ],
        entities: {
          actions_included_usage: "sensor.included",
          actions_estimated_minutes_remaining: "sensor.estimated",
        },
      },
      {
        "sensor.included": entity("sensor.included", "40", {
          unit_of_measurement: "min",
        }),
        "sensor.estimated": entity("sensor.estimated", "80", {
          unit_of_measurement: "min",
        }),
      },
    );
    expect(card.shadowRoot?.textContent).toContain("Included usage");
    expect(card.shadowRoot?.textContent).not.toContain(
      "Estimated equivalent minutes",
    );
  });

  it("announces budget warnings and blocked usage", async () => {
    const card = await renderCard(
      "github-insights-actions",
      {
        metrics: ["actions_cost"],
        entities: {
          actions_cost: "sensor.cost",
          actions_budget_warning: "binary_sensor.warning",
          actions_blocked: "binary_sensor.blocked",
        },
      },
      {
        "sensor.cost": entity("sensor.cost", "12", { currency: "USD" }),
        "binary_sensor.warning": entity("binary_sensor.warning", "on"),
        "binary_sensor.blocked": entity("binary_sensor.blocked", "on"),
      },
    );
    const alert = card.shadowRoot?.querySelector('[role="alert"]');
    expect(alert?.textContent).toContain("Actions blocked");
  });

  it("provides keyboard focus and accessible progress semantics", async () => {
    const card = await renderCard(
      "github-insights-overview",
      {
        metrics: ["actions_usage_percent"],
        entities: { actions_usage_percent: "sensor.usage" },
      },
      {
        "sensor.usage": entity("sensor.usage", "75", {
          unit_of_measurement: "%",
        }),
      },
    );
    const shell = card.shadowRoot?.querySelector("ha-card");
    const progress = card.shadowRoot?.querySelector('[role="progressbar"]');
    expect(shell?.getAttribute("tabindex")).toBe("0");
    expect(progress?.getAttribute("aria-valuenow")).toBe("75");
  });

  it("includes responsive and reduced-motion styles", () => {
    expect(cardStyles.cssText).toContain("@media (max-width: 520px)");
    expect(cardStyles.cssText).toContain(
      "@media (prefers-reduced-motion: reduce)",
    );
  });
});
