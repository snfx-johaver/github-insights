import { LitElement, html, nothing, type PropertyValues } from "lit";
import type {
  CardAction,
  CardDefinition,
  DiscoveredEntity,
  GitHubInsightsCardConfig,
} from "../models/config";
import type {
  HassEntity,
  HomeAssistant,
  LovelaceCardElement,
} from "../models/home-assistant";
import { metricDefinition } from "../models/metrics";
import {
  entitiesByKey,
  EntityDiscoveryService,
} from "../services/entity-discovery";
import { cardStyles } from "../styles/card-styles";
import { normalizeConfig, stubConfig } from "../utilities/config";
import {
  entityAvailable,
  formatMetric,
  numericState,
  safeHttpUrl,
  severityClass,
} from "../utilities/format";

export class GitHubInsightsCard extends LitElement {
  static styles = cardStyles;
  static properties = {
    hass: { attribute: false },
    config: { attribute: false },
    discovered: { attribute: false, state: true },
    discoveryError: { attribute: false, state: true },
    discoveryComplete: { attribute: false, state: true },
    companionCards: { attribute: false, state: true },
  };

  hass?: HomeAssistant;
  config?: GitHubInsightsCardConfig;
  discovered: DiscoveredEntity[] = [];
  discoveryError?: string;
  discoveryComplete = false;
  companionCards: LovelaceCardElement[] = [];
  definition!: CardDefinition;
  private discoveryGeneration = 0;
  private companionSignature = "";
  private holdTimer?: number;
  private lastTap = 0;

  setConfig(config: GitHubInsightsCardConfig): void {
    this.config = normalizeConfig(config, this.definition);
    this.setAttribute("layout", this.config.layout ?? "responsive");
    void this.refreshDiscovery();
  }

  static getStubConfig(): GitHubInsightsCardConfig {
    throw new Error("Card registration must provide getStubConfig.");
  }

  static getConfigElement(): HTMLElement {
    throw new Error("Card registration must provide getConfigElement.");
  }

  getCardSize(): number {
    const count = this.config?.metrics?.length ?? this.definition.defaultMetrics.length;
    return Math.max(2, Math.ceil(count / 2) + 1);
  }

  protected updated(changed: PropertyValues<this>): void {
    if (changed.has("hass")) void this.refreshDiscovery();
  }

  private async refreshDiscovery(): Promise<void> {
    if (!this.hass || !this.config) return;
    const generation = ++this.discoveryGeneration;
    this.discoveryComplete = false;
    try {
      const discovered = await EntityDiscoveryService.discover(
        this.hass,
        this.config,
      );
      if (generation === this.discoveryGeneration) {
        this.discovered = discovered;
        this.discoveryError = undefined;
        this.discoveryComplete = true;
        await this.refreshCompanionCards(generation);
      }
    } catch (error) {
      if (generation === this.discoveryGeneration) {
        this.discovered = [];
        this.discoveryError =
          error instanceof Error ? error.message : "Entity discovery failed.";
        this.discoveryComplete = true;
      }
    }
  }

  private resolveEntity(key: string): HassEntity | undefined {
    const reference = this.resolveEntityReference(key);
    return reference ? this.hass?.states[reference.entityId] : undefined;
  }

  private resolveEntityReference(key: string): DiscoveredEntity | undefined {
    const candidates = this.config?.repository
      ? this.discovered.filter(
          (entity) => entity.repository === this.config?.repository,
        )
      : this.discovered;
    return entitiesByKey(candidates).get(key);
  }

  private async refreshCompanionCards(generation: number): Promise<void> {
    if (this.definition.kind !== "dashboard" || !window.loadCardHelpers) {
      this.companionCards = [];
      this.companionSignature = "";
      return;
    }

    const configs: Record<string, unknown>[] = [];
    const chipKeys = [
      "workflow_health",
      "open_pull_requests",
      "dependabot_alerts",
      "last_successful_sync",
    ];
    const chips = chipKeys.flatMap((key) => {
      const reference = this.resolveEntityReference(key);
      if (!reference) return [];
      const metric = metricDefinition(key);
      return [{
        type: "entity",
        entity: reference.entityId,
        icon: metric.icon,
        content_info: "state",
      }];
    });
    if (customElements.get("mushroom-chips-card") && chips.length > 0) {
      configs.push({
        type: "custom:mushroom-chips-card",
        alignment: "justify",
        chips,
      });
    }

    const trendKeys = [
      "commits",
      "pull_requests_merged",
    ];
    const series = trendKeys.flatMap((key) => {
      const reference = this.resolveEntityReference(key);
      if (!reference) return [];
      return [{
        entity: reference.entityId,
        name: metricDefinition(key).label,
        type: "line",
        stroke_width: 3,
        group_by: { duration: "1d", func: "max", fill: "last" },
        show: { in_header: true, legend_value: false },
      }];
    });
    if (customElements.get("apexcharts-card") && series.length > 0) {
      configs.push({
        type: "custom:apexcharts-card",
        graph_span: "30d",
        update_interval: "5min",
        header: {
          show: true,
          title: "Engineering pulse",
          show_states: true,
          colorize_states: true,
        },
        apex_config: {
          chart: {
            height: 280,
            toolbar: { show: false },
            zoom: { enabled: false },
          },
          grid: { borderColor: "rgba(127, 127, 127, 0.16)" },
          legend: { show: true, position: "top" },
          stroke: { curve: "smooth" },
        },
        series,
      });
    }

    if (configs.length === 0) {
      this.companionCards = [];
      this.companionSignature = "";
      return;
    }

    const signature = JSON.stringify(configs);
    if (signature === this.companionSignature) {
      for (const card of this.companionCards) card.hass = this.hass;
      return;
    }

    try {
      const helpers = await window.loadCardHelpers();
      if (generation !== this.discoveryGeneration) return;
      this.companionCards = configs.map((config) => {
        const card = helpers.createCardElement(config);
        card.hass = this.hass;
        return card;
      });
      this.companionSignature = signature;
    } catch {
      this.companionCards = [];
      this.companionSignature = "";
    }
  }

  private sparklineTemplate(entity: HassEntity | undefined, label: string) {
    const raw = entity?.attributes.trend;
    const values = Array.isArray(raw)
      ? raw.filter((value): value is number => typeof value === "number")
      : [];
    if (values.length < 2) return nothing;
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    const range = Math.max(maximum - minimum, 1);
    const points = values
      .map((value, index) => {
        const x = (index / (values.length - 1)) * 100;
        const y = 30 - ((value - minimum) / range) * 28;
        return `${x},${y}`;
      })
      .join(" ");
    return html`
      <svg viewBox="0 0 100 32" role="img" aria-label="${label} trend">
        <title>${label} trend from ${minimum} to ${maximum}</title>
        <polyline
          points=${points}
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          vector-effect="non-scaling-stroke"
        ></polyline>
      </svg>
    `;
  }

  private metricTemplate(key: string) {
    const definition = metricDefinition(key);
    const entity = this.resolveEntity(key);
    const available = entityAvailable(entity);
    const value = numericState(entity);
    const severity =
      definition.format === "percent"
        ? severityClass(value, this.config?.severity)
        : "neutral";
    const estimated = definition.estimated ? "Estimated · " : "";
    const source = String(entity?.attributes.source ?? "");
    const unavailableReason = String(
      entity?.attributes.availability_reason ?? "Metric is not exposed for the current permissions or capability.",
    );
    return html`
      <article
        class="metric ${severity} ${available ? "" : "unavailable"}"
        aria-label="${definition.label}: ${formatMetric(this.hass, entity, definition)}"
      >
        <div class="metric-heading">
          <ha-icon .icon=${definition.icon} aria-hidden="true"></ha-icon>
          <span class="label">${definition.label}</span>
        </div>
        <strong class="value">${formatMetric(this.hass, entity, definition)}</strong>
        ${available
          ? html`<span class="meta">${estimated}${source}</span>`
          : html`<span class="meta">${unavailableReason}</span>`}
        ${definition.format === "percent" && value !== undefined
          ? html`<div
              class="bar"
              role="progressbar"
              aria-label=${definition.label}
              aria-valuemin="0"
              aria-valuemax="100"
              aria-valuenow=${Math.max(0, Math.min(100, value))}
            ><span style=${`--progress:${Math.max(0, Math.min(100, value))}%`}></span></div>`
          : nothing}
        ${this.sparklineTemplate(entity, definition.label)}
      </article>
    `;
  }

  private repositoryTemplate() {
    const selected =
      this.config?.repositories === "auto"
        ? undefined
        : new Set(this.config?.repositories ?? []);
    const discoveredRepositories = this.discovered
      .filter((entity) => entity.repository)
      .filter((entity) => !selected || selected.has(entity.repository ?? ""))
      .map((entity) => entity.repository as string)
      .filter((value, index, all) => all.indexOf(value) === index);
    const search = this.config?.search?.trim().toLocaleLowerCase();
    const included = new Set(this.config?.include?.names ?? []);
    const excluded = new Set(this.config?.exclude?.names ?? []);
    const favorites = new Set(this.config?.favorites ?? []);
    const repositories = discoveredRepositories
      .filter((repository) => !search || repository.toLocaleLowerCase().includes(search))
      .filter((repository) => included.size === 0 || included.has(repository))
      .filter((repository) => !excluded.has(repository))
      .sort((a, b) => {
        const favoriteDifference =
          Number(favorites.has(b)) - Number(favorites.has(a));
        return favoriteDifference || a.localeCompare(b);
      });

    if (repositories.length === 0) return nothing;
    return html`
      <section class="repositories ${this.definition.kind === "dashboard" ? "dashboard-repositories" : ""}" aria-label="Discovered repositories">
        ${this.definition.kind === "dashboard"
          ? html`<div class="section-heading">
              <div>
                <span class="eyebrow">Portfolio</span>
                <h3>Repositories</h3>
              </div>
              <span class="count">${repositories.length}</span>
            </div>`
          : nothing}
        <div class="repository-list">
        ${repositories.map(
          (repository) => html`
            <article class="repository">
              <ha-icon icon="mdi:source-repository" aria-hidden="true"></ha-icon>
              <strong>${favorites.has(repository) ? "★ " : ""}${repository}</strong>
              <span class="meta">${this.config?.group_by === "organization"
                ? repository.split("/", 1)[0]
                : "GitHub repository"}</span>
            </article>
          `,
        )}
        </div>
      </section>
    `;
  }

  private dashboardHeaderTemplate(account: HassEntity | undefined) {
    const avatarUrl = safeHttpUrl(account?.attributes.avatar_url);
    const blocked = this.resolveEntity("actions_blocked")?.state === "on";
    const warning = this.resolveEntity("actions_budget_warning")?.state === "on";
    const status = blocked ? "Blocked" : warning ? "Attention" : "Operational";
    const statusClass = blocked ? "critical" : warning ? "warning" : "healthy";
    return html`
      <header class="dashboard-hero">
        <div class="hero-glow" aria-hidden="true"></div>
        <div class="hero-copy">
          <span class="eyebrow">Live GitHub operations</span>
          <div class="hero-title">
            ${avatarUrl
              ? html`<img
                  src=${avatarUrl}
                  alt=""
                  width="52"
                  height="52"
                  loading="lazy"
                  referrerpolicy="no-referrer"
                />`
              : html`<span class="hero-mark"><ha-icon icon="mdi:github"></ha-icon></span>`}
            <div>
              <h2>${this.config?.title ?? "Engineering command center"}</h2>
              <p>Delivery, spend, adoption, and risk in one view.</p>
            </div>
          </div>
        </div>
        <span class="health-pill ${statusClass}">
          <span aria-hidden="true"></span>${status}
        </span>
      </header>
    `;
  }

  private dashboardMetricsTemplate(metrics: string[]) {
    const groups: Array<{ title: string; icon: string; keys: string[] }> = [
      {
        title: "Usage & spend",
        icon: "mdi:chart-donut",
        keys: ["actions_usage_percent", "actions_budget_percent", "copilot_paid_usage", "actions_cost"],
      },
      {
        title: "Delivery",
        icon: "mdi:rocket-launch-outline",
        keys: ["public_repositories", "open_pull_requests", "workflow_health", "commits"],
      },
      {
        title: "Risk & freshness",
        icon: "mdi:shield-check-outline",
        keys: ["dependabot_alerts", "code_scanning_alerts", "secret_scanning_alerts", "last_successful_sync"],
      },
    ];
    const configured = new Set(metrics);
    const grouped = new Set(groups.flatMap((group) => group.keys));
    const remaining = metrics.filter((key) => !grouped.has(key));
    if (remaining.length > 0) {
      groups.push({
        title: "More insights",
        icon: "mdi:view-grid-plus-outline",
        keys: remaining,
      });
    }
    return html`
      <div class="dashboard-sections">
        ${groups.map((group) => {
          const keys = group.keys.filter((key) => configured.has(key));
          if (keys.length === 0) return nothing;
          return html`
            <section class="dashboard-section">
              <div class="section-heading">
                <div class="section-title">
                  <ha-icon .icon=${group.icon}></ha-icon>
                  <h3>${group.title}</h3>
                </div>
              </div>
              <div class="grid">${keys.map((key) => this.metricTemplate(key))}</div>
            </section>
          `;
        })}
      </div>
    `;
  }

  private companionCardsTemplate() {
    if (this.definition.kind !== "dashboard" || this.companionCards.length === 0) {
      return nothing;
    }
    for (const card of this.companionCards) card.hass = this.hass;
    return html`
      <section
        class="companion-grid"
        aria-label="Optional dashboard visualizations"
        @pointerdown=${(event: Event) => event.stopPropagation()}
        @pointerup=${(event: Event) => event.stopPropagation()}
        @contextmenu=${(event: Event) => event.stopPropagation()}
      >
        ${this.companionCards}
      </section>
    `;
  }

  private heatmapTemplate() {
    if (this.definition.kind !== "contributions") return nothing;
    const entity = this.resolveEntity("contributions");
    const raw = entity?.attributes.calendar;
    const values = Array.isArray(raw)
      ? raw.filter((value): value is number => typeof value === "number").slice(-91)
      : [];
    if (values.length === 0) return nothing;
    const maximum = Math.max(...values, 1);
    return html`
      <div class="heatmap" role="img" aria-label="Contribution activity heatmap">
        ${values.map(
          (value) =>
            html`<span
              title=${`${value} contributions`}
              style=${`--intensity:${Math.ceil((value / maximum) * 4)}`}
            ></span>`,
        )}
      </div>
    `;
  }

  private statusTemplate() {
    if (this.discoveryError) {
      return html`<div class="status error" role="alert">
        <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
        <span>${this.discoveryError}</span>
      </div>`;
    }
    const blocked = this.resolveEntity("actions_blocked");
    if (blocked?.state === "on") {
      return html`<div class="status blocked" role="alert">
        <ha-icon icon="mdi:block-helper"></ha-icon>
        <span><strong>Actions blocked.</strong> GitHub enforcement is preventing applicable usage.</span>
      </div>`;
    }
    const warning = this.resolveEntity("actions_budget_warning");
    if (warning?.state === "on") {
      return html`<div class="status warning" role="status">
        <ha-icon icon="mdi:alert-outline"></ha-icon>
        <span>GitHub Actions budget warning threshold reached.</span>
      </div>`;
    }
    const partial = this.discovered
      .map((entry) => this.hass?.states[entry.entityId])
      .find((entity) => entity?.attributes.error);
    if (partial) {
      return html`<div class="status warning" role="status">
        <ha-icon icon="mdi:cloud-alert-outline"></ha-icon>
        <span>Some GitHub data is stale or unavailable: ${String(partial.attributes.error)}</span>
      </div>`;
    }
    return nothing;
  }

  private actionFor(event: Event): CardAction | undefined {
    if (event.type === "contextmenu") return this.config?.hold_action;
    return this.config?.tap_action;
  }

  private async runAction(action: CardAction | undefined): Promise<void> {
    if (!action || action.action === "none") return;
    if (action.action === "navigate" && action.navigation_path) {
      history.pushState(null, "", action.navigation_path);
      window.dispatchEvent(new Event("location-changed"));
      return;
    }
    if (action.action === "url") {
      const url = safeHttpUrl(action.url_path);
      if (url) window.open(url, "_blank", "noopener,noreferrer");
      return;
    }
    if (action.action === "call-service" && action.service && this.hass?.callService) {
      const [domain, service] = action.service.split(".", 2);
      if (domain && service) {
        await this.hass.callService(domain, service, action.service_data);
      }
      return;
    }
    const entityId = action.entity ?? this.config?.entity;
    if (entityId) {
      this.dispatchEvent(
        new CustomEvent("hass-more-info", {
          bubbles: true,
          composed: true,
          detail: { entityId },
        }),
      );
    }
  }

  private handlePointerDown(): void {
    if (!this.config?.hold_action) return;
    this.holdTimer = window.setTimeout(() => {
      void this.runAction(this.config?.hold_action);
      this.holdTimer = undefined;
    }, 500);
  }

  private handlePointerUp(event: Event): void {
    if (this.holdTimer === undefined && this.config?.hold_action) return;
    if (this.holdTimer !== undefined) {
      window.clearTimeout(this.holdTimer);
      this.holdTimer = undefined;
    }
    const now = Date.now();
    if (now - this.lastTap < 300 && this.config?.double_tap_action) {
      this.lastTap = 0;
      void this.runAction(this.config.double_tap_action);
    } else {
      this.lastTap = now;
      void this.runAction(this.actionFor(event));
    }
  }

  protected render() {
    if (!this.config) return nothing;
    const metrics =
      this.definition.kind === "compact"
        ? [this.config.primary_metric, this.config.secondary_metric].filter(
            (value): value is string => Boolean(value),
          )
        : (this.config.metrics ?? this.definition.defaultMetrics).filter(
            (key) =>
              this.config?.show_estimated_minutes !== false ||
              !metricDefinition(key).estimated,
          );
    const anyConfigured = metrics.some((key) => this.resolveEntity(key));
    const account = this.resolveEntity("account");
    const isDashboard = this.definition.kind === "dashboard";
    const isLoading =
      Boolean(this.hass?.connection) &&
      !this.discoveryComplete &&
      !this.discoveryError;

    return html`
      <ha-card
        tabindex="0"
        role="group"
        aria-label=${this.config.title ?? this.definition.name}
        @pointerdown=${this.handlePointerDown}
        @pointerup=${this.handlePointerUp}
        @keydown=${(event: KeyboardEvent) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            void this.runAction(this.config?.tap_action);
          }
        }}
        @contextmenu=${(event: Event) => {
          event.preventDefault();
          void this.runAction(this.config?.hold_action);
        }}
      >
        <section class="card ${isDashboard ? "dashboard-card" : ""}">
          ${isDashboard
            ? this.dashboardHeaderTemplate(account)
            : html`<header class="header">
            <div class="account">
              ${safeHttpUrl(account?.attributes.avatar_url)
                ? html`<img
                    src=${safeHttpUrl(account?.attributes.avatar_url)}
                    alt=""
                    width="40"
                    height="40"
                    loading="lazy"
                    referrerpolicy="no-referrer"
                  />`
                : nothing}
              <div>
              <h2>${this.config.title ?? this.definition.name}</h2>
              <div class="subtitle">${this.definition.description}</div>
              </div>
            </div>
            <ha-icon .icon=${this.config.icon ?? this.definition.icon} aria-hidden="true"></ha-icon>
          </header>`}
          ${this.statusTemplate()}
          ${isLoading
            ? html`<div class="status" role="status">Discovering GitHub Insights entities…</div>`
            : nothing}
          ${!isLoading && !anyConfigured && !this.discoveryError
            ? html`<div class="status empty" role="status">
                No supported metrics are available. Enable the relevant GitHub capability or select entities in the card editor.
              </div>`
            : isDashboard
              ? this.dashboardMetricsTemplate(metrics)
              : html`<div class="grid">${metrics.map((key) => this.metricTemplate(key))}</div>`}
          ${this.companionCardsTemplate()}
          ${this.repositoryTemplate()} ${this.heatmapTemplate()}
        </section>
      </ha-card>
    `;
  }
}

export function createCardClass(definition: CardDefinition) {
  return class extends GitHubInsightsCard {
    definition = definition;

    static getStubConfig(): GitHubInsightsCardConfig {
      return stubConfig(definition);
    }

    static getConfigElement(): HTMLElement {
      return document.createElement(definition.editorTag);
    }
  };
}
