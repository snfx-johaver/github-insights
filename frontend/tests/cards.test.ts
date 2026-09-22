import { beforeEach, describe, expect, it, vi } from "vitest";

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

interface TestEditor extends HTMLElement {
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

async function renderDiscoveredRepositories(
  config: Partial<GitHubInsightsCardConfig>,
): Promise<TestCard> {
  const repositories = [
    { id: "alpha", name: "octo/alpha" },
    { id: "beta", name: "octo/beta" },
    { id: "zeta", name: "acme/zeta" },
  ];
  const states: HomeAssistant["states"] = {};
  const registry = repositories.flatMap((repository, repositoryIndex) =>
    ["stars", "last_push", "workflow_health"].map((key) => {
      const entityId = `sensor.${repository.id}_${key}`;
      states[entityId] = entity(entityId, key === "stars"
        ? String((repositoryIndex + 1) * 10)
        : key === "last_push"
          ? `2026-09-${10 + repositoryIndex}T10:00:00Z`
          : repositoryIndex === 1 ? "failure" : "success", {
        visibility: repositoryIndex === 2 ? "private" : "public",
        archived: repository.id === "zeta",
        fork: repository.id === "alpha",
        default_branch: "main",
        repository_url:
          repository.id === "beta"
            ? "http://github.example/octo/beta"
            : `https://github.example/${repository.name}`,
        actions_url: `https://github.example/${repository.name}/actions`,
        token: "must-not-appear",
      });
      return {
        entity_id: entityId,
        platform: "github_insights",
        unique_id: `${repositoryIndex + 1}_${key}`,
        device_id: repository.id,
      };
    }),
  );
  const card = document.createElement("github-insights-repositories") as TestCard;
  card.hass = {
    states,
    connection: {
      sendMessagePromise: async <T,>(message: Record<string, unknown>) =>
        (message.type === "config/entity_registry/list"
          ? registry
          : repositories.map((repository) => ({
              id: repository.id,
              name: repository.name,
            }))) as T,
    },
  };
  card.setConfig({
    type: "custom:github-insights-repositories",
    metrics: ["stars", "workflow_health"],
    ...config,
  });
  document.body.append(card);
  await card.updateComplete;
  await new Promise((resolve) => window.setTimeout(resolve, 0));
  await card.updateComplete;
  return card;
}

function queryAll<T extends Element>(
  root: ShadowRoot | null | undefined,
  selector: string,
): T[] {
  const matches: T[] = [];
  root?.querySelectorAll<T>(selector).forEach((match) => matches.push(match));
  return matches;
}

describe("GitHub Insights cards", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    vi.restoreAllMocks();
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
          "actions_discounted_usage",
          "actions_estimated_minutes_remaining",
        ],
        entities: {
          actions_discounted_usage: "sensor.discounted",
          actions_estimated_minutes_remaining: "sensor.estimated",
        },
      },
      {
        "sensor.discounted": entity("sensor.discounted", "40", {
          unit_of_measurement: "min",
        }),
        "sensor.estimated": entity("sensor.estimated", "80", {
          unit_of_measurement: "min",
        }),
      },
    );
    expect(card.shadowRoot?.textContent).toContain(
      "Discounted or included consumption",
    );
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

  it("renders compact and expanded repository presentations with badges and favorites", async () => {
    const card = await renderDiscoveredRepositories({
      view: "compact",
      show_archived: true,
      favorites: ["octo/alpha"],
      repository_overrides: {
        "octo/beta": {
          title: "Beta override",
          view: "expanded",
          metrics: ["stars"],
          favorite: true,
        },
      },
    });
    const repositories = queryAll<HTMLElement>(card.shadowRoot, ".repository");
    expect(repositories).toHaveLength(3);
    const alpha = repositories.find((row) => row.textContent?.includes("octo/alpha"));
    const beta = repositories.find((row) => row.textContent?.includes("Beta override"));
    expect(repositories.slice(0, 2).every((row) => row.textContent?.includes("★"))).toBe(true);
    expect(alpha?.classList).toContain("compact");
    expect(beta?.classList).toContain("expanded");
    expect(beta?.querySelectorAll(".metric")).toHaveLength(1);
    expect(card.shadowRoot?.textContent).toContain("public");
    expect(card.shadowRoot?.textContent).toContain("Branch:");
  });

  it("uses deterministic multi-key sorting after favorites", async () => {
    const card = await renderDiscoveredRepositories({
      favorites: ["acme/zeta"],
      show_archived: true,
      sort: [
        { field: "stars", direction: "descending", nulls: "last" },
        { field: "name", direction: "ascending", nulls: "last" },
      ],
    });
    const names = queryAll(card.shadowRoot, ".repository-heading").map((row) =>
      row.textContent?.replace(/\s+/g, " ").trim(),
    );
    expect(names[0]).toContain("acme/zeta");
    expect(names[1]).toContain("octo/beta");
    expect(names[2]).toContain("octo/alpha");
  });

  it("only renders HTTPS repository and GitHub deep links", async () => {
    const card = await renderDiscoveredRepositories({ view: "expanded" });
    const links = queryAll<HTMLAnchorElement>(card.shadowRoot, "a");
    expect(links.length).toBeGreaterThan(0);
    expect(links.every((link) => link.href.startsWith("https://"))).toBe(true);
    expect(links.some((link) => link.textContent === "octo/beta")).toBe(false);
    expect(links.some((link) => link.href.endsWith("/actions"))).toBe(true);
    expect(links.every((link) => link.rel === "noopener noreferrer")).toBe(true);
  });

  it("preserves the browser context menu on interactive GitHub links", async () => {
    const callService = vi.fn();
    const card = await renderCard(
      "github-insights-actions",
      {
        metrics: ["actions_cost"],
        entities: { actions_cost: "sensor.cost" },
        hold_action: { action: "call-service", service: "notify.test" },
      },
      {
        "sensor.cost": entity("sensor.cost", "12", {
          currency: "USD",
          actions_url: "https://github.example/octo/repo/actions",
        }),
      },
    );
    card.hass.callService = callService;
    const link = card.shadowRoot?.querySelector<HTMLAnchorElement>("a");
    const event = new MouseEvent("contextmenu", {
      bubbles: true,
      cancelable: true,
      composed: true,
    });

    expect(link?.dispatchEvent(event)).toBe(true);
    expect(event.defaultPrevented).toBe(false);
    expect(callService).not.toHaveBeenCalled();
  });

  it("shows and copies sanitized diagnostics without entity attributes", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    const card = await renderDiscoveredRepositories({
      show_debug: true,
      show_archived: true,
      tap_action: {
        action: "call-service",
        service: "notify.test",
        service_data: { secret: "must-not-appear" },
      },
    });
    const toggle = card.shadowRoot?.querySelector<HTMLButtonElement>(
      'button[aria-controls$="-diagnostics"]',
    );
    expect(toggle?.getAttribute("aria-expanded")).toBe("false");
    toggle?.click();
    await card.updateComplete;
    expect(toggle?.getAttribute("aria-expanded")).toBe("true");
    const diagnostics = card.shadowRoot?.querySelector("pre")?.textContent ?? "";
    expect(diagnostics).toContain('"entity"');
    expect(diagnostics).not.toContain("token");
    expect(diagnostics).not.toContain("must-not-appear");
    expect(diagnostics).not.toContain("octo/alpha");
    expect(diagnostics).not.toContain("sensor.alpha_stars");
    expect(diagnostics).toContain('"repository": "repository_');
    card.shadowRoot?.querySelector<HTMLButtonElement>(
      'button[aria-label="Copy sanitized diagnostics to clipboard"]',
    )?.click();
    await Promise.resolve();
    await card.updateComplete;
    expect(writeText).toHaveBeenCalledWith(diagnostics);
    expect(card.shadowRoot?.querySelector('[role="status"]')?.textContent).toContain(
      "Diagnostics copied",
    );
  });

  it("prominently labels configured allowance and authoritative costs", async () => {
    const card = await renderCard(
      "github-insights-actions",
      {
        metrics: [
          "actions_configured_included_minutes",
          "actions_configured_minutes_remaining",
          "actions_configured_minutes_used_percent",
          "actions_gross_cost",
          "actions_discount",
          "actions_cost",
        ],
        entities: {
          actions_configured_included_minutes: "sensor.allowance",
          actions_configured_minutes_remaining: "sensor.remaining",
          actions_configured_minutes_used_percent: "sensor.used_percent",
          actions_gross_cost: "sensor.gross",
          actions_discount: "sensor.discount",
          actions_cost: "sensor.net",
        },
      },
      {
        "sensor.allowance": entity("sensor.allowance", "2000", { unit_of_measurement: "min" }),
        "sensor.remaining": entity("sensor.remaining", "500", { unit_of_measurement: "min" }),
        "sensor.used_percent": entity("sensor.used_percent", "75", { unit_of_measurement: "%" }),
        "sensor.gross": entity("sensor.gross", "20", { currency: "USD" }),
        "sensor.discount": entity("sensor.discount", "8", { currency: "USD" }),
        "sensor.net": entity("sensor.net", "12", { currency: "USD" }),
      },
    );
    expect(card.shadowRoot?.querySelectorAll(".metric.prominent")).toHaveLength(6);
    expect(card.shadowRoot?.textContent).toContain("Configured allowance");
    expect(card.shadowRoot?.textContent).toContain("Source: Authoritative GitHub billing");
    const progress = card.shadowRoot?.querySelector('[role="progressbar"]');
    expect(progress?.getAttribute("aria-valuenow")).toBe("75");
    expect(progress?.getAttribute("aria-valuemin")).toBe("0");
    expect(progress?.getAttribute("aria-valuemax")).toBe("100");
  });

  it("announces over-quota percentages without expanding the visual bar", async () => {
    const card = await renderCard(
      "github-insights-actions",
      {
        metrics: ["actions_configured_minutes_used_percent"],
        entities: {
          actions_configured_minutes_used_percent: "sensor.used_percent",
        },
      },
      {
        "sensor.used_percent": entity("sensor.used_percent", "125", {
          unit_of_measurement: "%",
        }),
      },
    );
    const progress = card.shadowRoot?.querySelector('[role="progressbar"]');
    expect(progress?.getAttribute("aria-valuenow")).toBe("100");
    expect(progress?.getAttribute("aria-valuetext")).toBe("125% used");
  });

  it("applies visibility, archive, and fork repository filters", async () => {
    const card = await renderDiscoveredRepositories({
      include: { visibility: ["public"] },
      exclude: { archived: true, forked: true },
    });
    expect(card.shadowRoot?.querySelectorAll(".repository")).toHaveLength(1);
    expect(card.shadowRoot?.textContent).toContain("octo/beta");
    expect(card.shadowRoot?.textContent).not.toContain("octo/alpha");
    expect(card.shadowRoot?.textContent).not.toContain("acme/zeta");
  });

  it("sorts unavailable repository metrics last", async () => {
    const card = await renderDiscoveredRepositories({
      show_archived: true,
      sort: [{ field: "stars", direction: "descending", nulls: "last" }],
    });
    const unavailable = card.hass.states["sensor.beta_stars"];
    unavailable.state = "unavailable";
    card.hass = { ...card.hass, states: { ...card.hass.states } };
    await card.updateComplete;
    const names = queryAll(card.shadowRoot, ".repository-heading").map((row) =>
      row.textContent?.replace(/\s+/g, " ").trim(),
    );
    expect(names.at(-1)).toContain("octo/beta");
  });

  it("exposes picker-safe editor controls for repository display and diagnostics", async () => {
    const definition = CARD_DEFINITIONS.find((item) => item.kind === "repositories");
    expect(definition).toBeDefined();
    const editor = document.createElement(definition!.editorTag) as TestEditor;
    editor.setConfig({ type: `custom:${definition!.tag}` });
    document.body.append(editor);
    await editor.updateComplete;
    expect(editor.shadowRoot?.querySelector('[aria-label="Repository view"]')).toBeTruthy();
    expect(editor.shadowRoot?.querySelector('[aria-label="Favorite repositories"]')).toBeTruthy();
    expect(editor.shadowRoot?.querySelector('[aria-label="Primary repository sort"]')).toBeTruthy();
    expect(editor.shadowRoot?.textContent).toContain("Show sanitized diagnostics panel");
    expect(editor.shadowRoot?.textContent).toContain("Show metric attribute badges");
  });

  it("keeps a stable accessible compact-card snapshot", async () => {
    const card = await renderCard(
      "github-insights-compact",
      {
        title: "Actions snapshot",
        primary_metric: "actions_configured_minutes_used_percent",
        secondary_metric: "actions_cost",
        entities: {
          actions_configured_minutes_used_percent: "sensor.percent",
          actions_cost: "sensor.cost",
        },
      },
      {
        "sensor.percent": entity("sensor.percent", "25", { unit_of_measurement: "%" }),
        "sensor.cost": entity("sensor.cost", "4", { currency: "USD" }),
      },
    );
    expect(card.shadowRoot?.textContent?.replace(/\s+/g, " ").trim())
      .toMatchInlineSnapshot(
        `"Actions snapshot One primary and secondary metric for dense dashboards. Allowance used 25% Source: Configured allowance calculation Net cost $4.00 Source: Authoritative GitHub billing"`,
      );
  });

  it("includes responsive and reduced-motion styles", () => {
    expect(cardStyles.cssText).toContain("@media (max-width: 520px)");
    expect(cardStyles.cssText).toContain(
      "@media (prefers-reduced-motion: reduce)",
    );
  });
});
