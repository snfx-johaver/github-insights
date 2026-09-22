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
  };

  hass?: HomeAssistant;
  config?: GitHubInsightsCardConfig;
  discovered: DiscoveredEntity[] = [];
  discoveryError?: string;
  discoveryComplete = false;
  definition!: CardDefinition;
  private discoveryGeneration = 0;
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
    const candidates = this.config?.repository
      ? this.discovered.filter(
          (entity) => entity.repository === this.config?.repository,
        )
      : this.discovered;
    const reference = entitiesByKey(candidates).get(key);
    return reference ? this.hass?.states[reference.entityId] : undefined;
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
      <section class="repositories" aria-label="Discovered repositories">
        ${repositories.map(
          (repository) => html`
            <article class="repository">
              <strong>${favorites.has(repository) ? "★ " : ""}${repository}</strong>
              <span class="meta">${this.config?.group_by === "organization"
                ? repository.split("/", 1)[0]
                : "GitHub repository"}</span>
            </article>
          `,
        )}
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
    const avatarUrl = safeHttpUrl(account?.attributes.avatar_url);
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
        <section class="card">
          <header class="header">
            <div class="account">
              ${avatarUrl
                ? html`<img
                    src=${avatarUrl}
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
          </header>
          ${this.statusTemplate()}
          ${isLoading
            ? html`<div class="status" role="status">Discovering GitHub Insights entities…</div>`
            : nothing}
          ${!isLoading && !anyConfigured && !this.discoveryError
            ? html`<div class="status empty" role="status">
                No supported metrics are available. Enable the relevant GitHub capability or select entities in the card editor.
              </div>`
            : html`<div class="grid">${metrics.map((key) => this.metricTemplate(key))}</div>`}
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
