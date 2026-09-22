import { LitElement, css, html, nothing } from "lit";
import {
  INSIGHTS_SECTIONS,
  PRESET_CONFIGS,
} from "../cards/definitions";
import type {
  CardDefinition,
  GitHubInsightsCardConfig,
  InsightsPreset,
  InsightsSection,
  RepositoryDisplayOverride,
} from "../models/config";
import type { HomeAssistant } from "../models/home-assistant";
import { METRICS } from "../models/metrics";
import { normalizeConfig } from "../utilities/config";

export class GitHubInsightsEditor extends LitElement {
  static properties = {
    hass: { attribute: false },
    config: { attribute: false },
    overrideError: { attribute: false, state: true },
  };

  static styles = css`
    :host {
      display: grid;
      gap: 16px;
      padding: 8px 0;
      color: var(--primary-text-color);
    }
    label,
    fieldset {
      display: grid;
      gap: 6px;
    }
    fieldset {
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 12px;
    }
    input,
    select,
    textarea {
      min-height: 42px;
      padding: 0 10px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 8px;
    }
    textarea {
      min-height: 110px;
      padding-block: 8px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    }
    input:focus-visible,
    select:focus-visible,
    textarea:focus-visible,
    button:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    .options {
      display: grid;
      gap: 6px;
    }
    .ordered {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto auto;
      align-items: center;
      gap: 6px;
      min-height: 38px;
    }
    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 36px;
    }
    button {
      min-width: 36px;
      min-height: 36px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      color: var(--primary-text-color);
      background: var(--secondary-background-color);
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.45;
      cursor: default;
    }
    .error {
      color: var(--error-color);
    }
  `;

  hass?: HomeAssistant;
  config?: GitHubInsightsCardConfig;
  definition!: CardDefinition;
  overrideError = "";

  setConfig(config: GitHubInsightsCardConfig): void {
    this.config = normalizeConfig(config, this.definition);
  }

  private updateConfig(patch: Partial<GitHubInsightsCardConfig>): void {
    if (!this.config) return;
    this.config = normalizeConfig({ ...this.config, ...patch }, this.definition);
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        bubbles: true,
        composed: true,
        detail: { config: this.config },
      }),
    );
  }

  private moveItem<T>(values: T[], index: number, offset: -1 | 1): T[] {
    const target = index + offset;
    if (target < 0 || target >= values.length) return values;
    const reordered = [...values];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    return reordered;
  }

  private toggleMetric(key: string, checked: boolean): void {
    const metrics = [...(this.config?.metrics ?? [])];
    const index = metrics.indexOf(key);
    if (checked && index === -1) metrics.push(key);
    if (!checked && index !== -1) metrics.splice(index, 1);
    this.updateConfig({ metrics });
  }

  private toggleSection(section: InsightsSection, checked: boolean): void {
    const sections = [...(this.config?.sections ?? [])];
    const index = sections.indexOf(section);
    if (checked && index === -1) sections.push(section);
    if (!checked && index !== -1) sections.splice(index, 1);
    this.updateConfig({ sections });
  }

  private orderedToggle(
    label: string,
    checked: boolean,
    index: number,
    length: number,
    toggle: (checked: boolean) => void,
    move: (offset: -1 | 1) => void,
  ) {
    return html`
      <div class="ordered">
        <label class="check">
          <input
            type="checkbox"
            .checked=${checked}
            @change=${(event: Event) =>
              toggle((event.target as HTMLInputElement).checked)}
          />
          ${label}
        </label>
        <button
          type="button"
          aria-label=${`Move ${label} up`}
          ?disabled=${!checked || index <= 0}
          @click=${() => move(-1)}
        >↑</button>
        <button
          type="button"
          aria-label=${`Move ${label} down`}
          ?disabled=${!checked || index < 0 || index >= length - 1}
          @click=${() => move(1)}
        >↓</button>
      </div>
    `;
  }

  private insightsOptions() {
    if (!this.config || this.definition.kind !== "insights") return nothing;
    const sections = this.config.sections ?? [];
    const orderedSections = [
      ...sections,
      ...INSIGHTS_SECTIONS.filter((section) => !sections.includes(section)),
    ];
    return html`
      <label>
        Preset
        <select
          aria-label="Card preset"
          .value=${this.config.preset ?? "dashboard"}
          @change=${(event: Event) => {
            const preset = (event.target as HTMLSelectElement)
              .value as InsightsPreset;
            const defaults = PRESET_CONFIGS[preset];
            this.updateConfig({
              preset,
              metrics: [...defaults.metrics],
              sections: [...defaults.sections],
              layout: defaults.layout,
            });
          }}
        >
          ${Object.keys(PRESET_CONFIGS).map(
            (preset) =>
              html`<option value=${preset}>${preset.replaceAll("_", " ")}</option>`,
          )}
        </select>
      </label>
      <fieldset>
        <legend>Sections and order</legend>
        <div class="options">
          ${orderedSections.map((section) => {
            const index = sections.indexOf(section);
            return this.orderedToggle(
              section,
              index !== -1,
              index,
              sections.length,
              (checked) => this.toggleSection(section, checked),
              (offset) =>
                this.updateConfig({
                  sections: this.moveItem(sections, index, offset),
                }),
            );
          })}
        </div>
      </fieldset>
    `;
  }

  private repositoryOptions() {
    if (!this.config || this.definition.kind !== "repository") return nothing;
    const selectionMode = this.config.repository
      ? "single"
      : Array.isArray(this.config.repositories)
        ? "multiple"
        : "auto";
    return html`
      <label>
        Repository selection
        <select
          aria-label="Repository selection"
          .value=${selectionMode}
          @change=${(event: Event) => {
            const mode = (event.target as HTMLSelectElement).value;
            this.updateConfig(
              mode === "single"
                ? { repository: "", repositories: "auto" }
                : mode === "multiple"
                  ? { repository: undefined, repositories: [] }
                  : { repository: undefined, repositories: "auto" },
            );
          }}
        >
          <option value="auto">Auto-discovered collection</option>
          <option value="multiple">Selected repositories</option>
          <option value="single">One repository</option>
        </select>
      </label>
      ${selectionMode === "single"
        ? html`<label>
            Repository
            <input
              aria-label="Repository full name"
              placeholder="owner/repository"
              .value=${this.config.repository ?? ""}
              @input=${(event: Event) =>
                this.updateConfig({
                  repository:
                    (event.target as HTMLInputElement).value || undefined,
                })}
            />
          </label>`
        : nothing}
      ${selectionMode === "multiple"
        ? html`<label>
            Repositories
            <input
              aria-label="Selected repositories"
              placeholder="owner/one, owner/two"
              .value=${Array.isArray(this.config.repositories)
                ? this.config.repositories.join(", ")
                : ""}
              @change=${(event: Event) =>
                this.updateConfig({
                  repositories: (event.target as HTMLInputElement).value
                    .split(",")
                    .map((value) => value.trim())
                    .filter(Boolean),
                })}
            />
          </label>`
        : nothing}
      <label>
        Search repositories
        <input
          aria-label="Search repositories"
          .value=${this.config.search ?? ""}
          @input=${(event: Event) =>
            this.updateConfig({
              search: (event.target as HTMLInputElement).value || undefined,
            })}
        />
      </label>
      <label>
        Favorite repositories
        <input
          aria-label="Favorite repositories"
          placeholder="owner/one, owner/two"
          .value=${(this.config.favorites ?? []).join(", ")}
          @change=${(event: Event) =>
            this.updateConfig({
              favorites: (event.target as HTMLInputElement).value
                .split(",")
                .map((value) => value.trim())
                .filter(Boolean),
            })}
        />
      </label>
      <label>
        Primary repository sort
        <select
          aria-label="Primary repository sort"
          .value=${this.config.sort?.[0]?.field ?? "workflow_health"}
          @change=${(event: Event) => {
            const field = (event.target as HTMLSelectElement).value;
            this.updateConfig({
              sort: [
                {
                  field,
                  direction:
                    field === "last_push" || field === "stars"
                      ? "descending"
                      : "ascending",
                  nulls: "last",
                },
                { field: "name", direction: "ascending", nulls: "last" },
              ],
            });
          }}
        >
          ${["workflow_health", "last_push", "stars", "open_issues", "name"].map(
            (field) =>
              html`<option value=${field}>${field.replaceAll("_", " ")}</option>`,
          )}
        </select>
      </label>
      <label>
        Repository overrides (JSON)
        <textarea
          aria-label="Repository overrides"
          .value=${JSON.stringify(this.config.repository_overrides ?? {}, null, 2)}
          @change=${(event: Event) => {
            try {
              const value = JSON.parse(
                (event.target as HTMLTextAreaElement).value || "{}",
              ) as Record<string, RepositoryDisplayOverride>;
              this.overrideError = "";
              this.updateConfig({ repository_overrides: value });
            } catch {
              this.overrideError = "Repository overrides must be valid JSON.";
            }
          }}
        ></textarea>
        ${this.overrideError
          ? html`<span class="error" role="alert">${this.overrideError}</span>`
          : nothing}
      </label>
    `;
  }

  protected render() {
    if (!this.config) return nothing;
    const metrics = this.config.metrics ?? [];
    const layouts =
      this.definition.kind === "repository"
        ? ["responsive", "compact", "expanded", "detail"]
        : ["responsive", "compact", "expanded"];
    const metricDefinitions = Object.values(METRICS);
    const orderedMetrics = [
      ...metrics
        .map((key) => METRICS[key])
        .filter((metric) => metric !== undefined),
      ...metricDefinitions.filter((metric) => !metrics.includes(metric.key)),
    ];
    return html`
      <label>
        Title
        <input
          aria-label="Card title"
          .value=${this.config.title ?? ""}
          @input=${(event: Event) =>
            this.updateConfig({
              title: (event.target as HTMLInputElement).value || undefined,
            })}
        />
      </label>
      ${this.insightsOptions()}
      <label>
        Presentation
        <select
          aria-label="Card presentation"
          .value=${this.config.layout ?? this.definition.defaultLayout}
          @change=${(event: Event) =>
            this.updateConfig({
              layout: (event.target as HTMLSelectElement)
                .value as GitHubInsightsCardConfig["layout"],
            })}
        >
          ${layouts.map(
            (layout) => html`<option value=${layout}>${layout}</option>`,
          )}
        </select>
      </label>
      ${this.repositoryOptions()}
      <fieldset>
        <legend>Metrics and order</legend>
        <div class="options">
          ${orderedMetrics.map((metric) => {
            const index = metrics.indexOf(metric.key);
            return this.orderedToggle(
              `${metric.label}${metric.estimated ? " (estimated)" : ""}`,
              index !== -1,
              index,
              metrics.length,
              (checked) => this.toggleMetric(metric.key, checked),
              (offset) =>
                this.updateConfig({
                  metrics: this.moveItem(metrics, index, offset),
                }),
            );
          })}
        </div>
      </fieldset>
      <fieldset>
        <legend>Display options</legend>
        ${this.checkbox(
          "Show estimated equivalent minutes",
          this.config.show_estimated_minutes ?? true,
          (show_estimated_minutes) =>
            this.updateConfig({ show_estimated_minutes }),
        )}
        ${this.checkbox(
          "Show forecast when supplied by GitHub Insights",
          this.config.show_forecast ?? true,
          (show_forecast) => this.updateConfig({ show_forecast }),
        )}
        ${this.checkbox(
          "Show metric attribute badges",
          this.config.show_metric_badges ?? true,
          (show_metric_badges) => this.updateConfig({ show_metric_badges }),
        )}
        <label>
          Badge attributes
          <input
            aria-label="Metric badge attributes"
            placeholder="visibility, default_branch"
            .value=${(this.config.metric_badges ?? [])
              .map((badge) => badge.attribute)
              .join(", ")}
            @change=${(event: Event) =>
              this.updateConfig({
                metric_badges: (event.target as HTMLInputElement).value
                  .split(",")
                  .map((attribute) => attribute.trim())
                  .filter(Boolean)
                  .map((attribute) => ({ attribute })),
              })}
          />
        </label>
        ${this.checkbox(
          "Show sanitized diagnostics panel",
          this.config.show_debug ?? false,
          (show_debug) => this.updateConfig({ show_debug }),
        )}
      </fieldset>
    `;
  }

  private checkbox(
    label: string,
    checked: boolean,
    update: (checked: boolean) => void,
  ) {
    return html`<label class="check">
      <input
        type="checkbox"
        .checked=${checked}
        @change=${(event: Event) =>
          update((event.target as HTMLInputElement).checked)}
      />
      ${label}
    </label>`;
  }
}

export function createEditorClass(definition: CardDefinition) {
  return class extends GitHubInsightsEditor {
    definition = definition;
  };
}
