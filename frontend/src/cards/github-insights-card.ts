import { LitElement, html, nothing, type PropertyValues } from "lit";
import type {
  CardAction,
  CardDefinition,
  DiscoveredEntity,
  GitHubInsightsCardConfig,
  MetricBadgeConfig,
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
  safeHttpsUrl,
  safeText,
  severityClass,
} from "../utilities/format";
import {
  buildRepositories,
  type RepositoryModel,
} from "../utilities/repositories";

export class GitHubInsightsCard extends LitElement {
  static styles = cardStyles;
  static properties = {
    hass: { attribute: false },
    config: { attribute: false },
    discovered: { attribute: false, state: true },
    discoveryError: { attribute: false, state: true },
    discoveryComplete: { attribute: false, state: true },
    debugExpanded: { attribute: false, state: true },
    copyStatus: { attribute: false, state: true },
  };

  hass?: HomeAssistant;
  config?: GitHubInsightsCardConfig;
  discovered: DiscoveredEntity[] = [];
  discoveryError?: string;
  discoveryComplete = false;
  debugExpanded = false;
  copyStatus = "";
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

  private metricLink(key: string, entity: HassEntity | undefined): string | undefined {
    const attributes = entity?.attributes ?? {};
    const candidates = key.includes("workflow") || key.startsWith("actions_")
      ? [attributes.actions_url, attributes.workflow_url, attributes.html_url]
      : key.includes("issue")
        ? [attributes.issues_url, attributes.html_url]
        : key.includes("pull")
          ? [attributes.pulls_url, attributes.html_url]
          : key.includes("alert") || key.includes("scanning")
            ? [attributes.security_url, attributes.html_url]
            : [attributes.html_url, attributes.url];
    return candidates.map(safeHttpsUrl).find(Boolean);
  }

  private badgeTemplate(entity: HassEntity | undefined, badges: MetricBadgeConfig[]) {
    if (this.config?.show_metric_badges === false || badges.length === 0) return nothing;
    const rendered = badges.flatMap((badge) => {
      const value = safeText(entity?.attributes[badge.attribute], 60);
      if (!value) return [];
      const name = badge.label ?? badge.attribute.replaceAll("_", " ");
      return [html`
        <span class="badge" aria-label=${`${name}: ${value}`}>
          ${badge.icon
            ? html`<ha-icon .icon=${badge.icon} aria-hidden="true"></ha-icon><span class="sr-only">${name}:</span>`
            : html`<span class="badge-label">${name}:</span>`}
          ${value}
        </span>
      `];
    });
    return rendered.length ? html`<div class="badges">${rendered}</div>` : nothing;
  }

  private metricTemplate(
    key: string,
    suppliedEntity?: HassEntity,
    badges: MetricBadgeConfig[] = this.config?.metric_badges ?? [],
    repositoryScoped = false,
  ) {
    const definition = metricDefinition(key);
    const entity = repositoryScoped ? suppliedEntity : suppliedEntity ?? this.resolveEntity(key);
    const available = entityAvailable(entity);
    const value = numericState(entity);
    const severity =
      definition.format === "percent"
        ? severityClass(value, this.config?.severity)
        : "neutral";
    const estimated = definition.estimated ? "Estimated · " : "";
    const source = safeText(entity?.attributes.source, 100) ?? definition.sourceLabel ?? "";
    const unavailableReason = String(
      entity?.attributes.availability_reason ?? "Metric is not exposed for the current permissions or capability.",
    );
    return html`
      <article
        class="metric ${severity} ${available ? "" : "unavailable"} ${definition.prominent ? "prominent" : ""}"
        aria-label="${definition.label}: ${formatMetric(this.hass, entity, definition)}"
      >
        <div class="metric-heading">
          <ha-icon .icon=${definition.icon} aria-hidden="true"></ha-icon>
          ${this.metricLink(key, entity)
            ? html`<a
                class="metric-link"
                href=${this.metricLink(key, entity)}
                target="_blank"
                rel="noopener noreferrer"
                aria-label=${`${definition.label} on GitHub (opens in a new tab)`}
                @pointerdown=${(event: Event) => event.stopPropagation()}
                @pointerup=${(event: Event) => event.stopPropagation()}
              >${definition.label}</a>`
            : html`<span class="label">${definition.label}</span>`}
        </div>
        <strong class="value">${formatMetric(this.hass, entity, definition)}</strong>
        ${available
          ? estimated || source
            ? html`<span class="meta">${estimated}${source ? `Source: ${source}` : ""}</span>`
            : nothing
          : html`<span class="meta">${unavailableReason}</span>`}
        ${this.badgeTemplate(entity, badges)}
        ${definition.format === "percent" && value !== undefined
          ? html`<div
              class="bar"
              role="progressbar"
              aria-label=${definition.label}
              aria-valuemin="0"
              aria-valuemax="100"
              aria-valuenow=${Math.max(0, Math.min(100, value))}
              aria-valuetext=${`${formatMetric(this.hass, entity, definition)} used`}
            ><span style=${`--progress:${Math.max(0, Math.min(100, value))}%`}></span></div>`
          : nothing}
        ${this.sparklineTemplate(entity, definition.label)}
      </article>
    `;
  }

  private repositoryUrl(repository: RepositoryModel): string | undefined {
    for (const entity of repository.entities.values()) {
      const url = safeHttpsUrl(
        entity.attributes.repository_url,
      );
      if (url) return url;
    }
    return undefined;
  }

  private repositoryTemplate() {
    if (!this.config) return nothing;
    let repositories = buildRepositories(this.discovered, this.hass, this.config);
    if (this.definition.kind === "repository" && this.config.repository) {
      repositories = repositories.filter(
        (repository) => repository.name === this.config?.repository,
      );
    }

    if (repositories.length === 0) return nothing;
    return html`
      <section class="repositories" aria-label="Discovered repositories">
        ${repositories.map(
          (repository) => {
            const view = repository.override?.view ?? this.config?.view ?? "compact";
            const metrics =
              repository.override?.metrics ?? this.config?.metrics ?? this.definition.defaultMetrics;
            const configuredBadges =
              repository.override?.metric_badges ?? this.config?.metric_badges;
            const badges = configuredBadges?.length
              ? configuredBadges
              : [
                  { attribute: "visibility", icon: "mdi:eye-outline" },
                  { attribute: "default_branch", label: "Branch" },
                ];
            const url = this.repositoryUrl(repository);
            return html`
            <article class="repository ${view}">
              <div class="repository-heading">
                <span class="favorite" aria-label=${repository.favorite ? "Favorite repository" : "Repository"}>
                  ${repository.favorite ? "★" : ""}
                </span>
                ${url
                  ? html`<a
                      href=${url}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label=${`${repository.title} on GitHub (opens in a new tab)`}
                      @pointerdown=${(event: Event) => event.stopPropagation()}
                      @pointerup=${(event: Event) => event.stopPropagation()}
                    >${repository.title}</a>`
                  : html`<strong>${repository.title}</strong>`}
                <span class="meta">${this.config?.group_by === "organization"
                  ? repository.name.split("/", 1)[0]
                  : view === "expanded" ? "Expanded repository details" : "GitHub repository"}</span>
              </div>
              <div class="repository-metrics" aria-label=${`${repository.title} metrics`}>
                ${metrics.map((key) =>
                  this.metricTemplate(key, repository.entities.get(key), badges, true),
                )}
              </div>
            </article>
          `},
        )}
      </section>
    `;
  }

  private diagnosticsPayload(): string {
    if (!this.config) return "{}";
    const config = {
      type: this.config.type,
      layout: this.config.layout,
      view: this.config.view,
      metrics: this.config.metrics,
      sort: this.config.sort,
      repository_selection_count: Array.isArray(this.config.repositories)
        ? this.config.repositories.length
        : this.config.repositories,
      favorite_count: this.config.favorites?.length ?? 0,
      include_name_count: this.config.include?.names?.length ?? 0,
      include_visibility: this.config.include?.visibility,
      exclude_name_count: this.config.exclude?.names?.length ?? 0,
      exclude_archived: this.config.exclude?.archived,
      exclude_forked: this.config.exclude?.forked,
      repository_override_count: Object.keys(
        this.config.repository_overrides ?? {},
      ).length,
      show_metric_badges: this.config.show_metric_badges,
      metric_badges: this.config.metric_badges,
    };
    const repositoryAliases = new Map<string, string>();
    const entityAliases = new Map<string, string>();
    const alias = (values: Map<string, string>, value: string, prefix: string) => {
      const current = values.get(value);
      if (current) return current;
      const created = `${prefix}_${values.size + 1}`;
      values.set(value, created);
      return created;
    };
    const entities = this.discovered
      .map(({ key, entityId, repository }) => ({
        key,
        entity: alias(entityAliases, entityId, "entity"),
        repository: repository
          ? alias(repositoryAliases, repository, "repository")
          : undefined,
      }))
      .sort((a, b) =>
        `${a.repository ?? ""}:${a.key}:${a.entity}`.localeCompare(
          `${b.repository ?? ""}:${b.key}:${b.entity}`,
        ),
      );
    return JSON.stringify({ config, entities }, null, 2);
  }

  private diagnosticsTemplate() {
    if (!this.config?.show_debug) return nothing;
    const panelId = `${this.definition.tag}-diagnostics`;
    return html`
      <section class="diagnostics">
        <button
          type="button"
          aria-expanded=${String(this.debugExpanded)}
          aria-controls=${panelId}
          @click=${(event: Event) => {
            event.stopPropagation();
            this.debugExpanded = !this.debugExpanded;
          }}
        >
          ${this.debugExpanded ? "Hide" : "Show"} diagnostics
        </button>
        ${this.debugExpanded
          ? html`<div id=${panelId}>
              <p class="meta">Sanitized resolved configuration and discovered entity mapping.</p>
              <pre tabindex="0">${this.diagnosticsPayload()}</pre>
              <button
                type="button"
                aria-label="Copy sanitized diagnostics to clipboard"
                @click=${async (event: Event) => {
                  event.stopPropagation();
                  try {
                    await navigator.clipboard.writeText(this.diagnosticsPayload());
                    this.copyStatus = "Diagnostics copied.";
                  } catch {
                    this.copyStatus = "Unable to copy diagnostics.";
                  }
                }}
              >Copy diagnostics</button>
              <span class="sr-only" role="status" aria-live="polite">${this.copyStatus}</span>
            </div>`
          : nothing}
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

  private handlePointerDown(event: Event): void {
    if ((event.composedPath()[0] as Element | undefined)?.closest?.("a,button")) return;
    if (!this.config?.hold_action) return;
    this.holdTimer = window.setTimeout(() => {
      void this.runAction(this.config?.hold_action);
      this.holdTimer = undefined;
    }, 500);
  }

  private handlePointerUp(event: Event): void {
    if ((event.composedPath()[0] as Element | undefined)?.closest?.("a,button")) return;
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
    const isRepositoryCard =
      this.definition.kind === "repositories" || this.definition.kind === "repository";
    const hasRepositories =
      isRepositoryCard &&
      buildRepositories(this.discovered, this.hass, this.config).some(
        (repository) =>
          this.definition.kind !== "repository" ||
          !this.config?.repository ||
          repository.name === this.config.repository,
      );
    const account = this.resolveEntity("account");
    const avatarUrl = safeHttpsUrl(account?.attributes.avatar_url);
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
          if (event.target === event.currentTarget && (event.key === "Enter" || event.key === " ")) {
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
          ${!isLoading && !anyConfigured && !hasRepositories && !this.discoveryError
            ? html`<div class="status empty" role="status">
                No supported metrics are available. Enable the relevant GitHub capability or select entities in the card editor.
              </div>`
            : isRepositoryCard
              ? nothing
              : html`<div class="grid">${metrics.map((key) => this.metricTemplate(key))}</div>`}
          ${this.repositoryTemplate()} ${this.heatmapTemplate()} ${this.diagnosticsTemplate()}
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
