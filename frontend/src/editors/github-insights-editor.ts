import { LitElement, css, html, nothing } from "lit";
import type {
  CardDefinition,
  GitHubInsightsCardConfig,
} from "../models/config";
import type { HomeAssistant } from "../models/home-assistant";
import { METRICS } from "../models/metrics";
import { normalizeConfig } from "../utilities/config";

export class GitHubInsightsEditor extends LitElement {
  static properties = {
    hass: { attribute: false },
    config: { attribute: false },
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
    select {
      min-height: 42px;
      padding: 0 10px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 8px;
    }
    .metrics {
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    }
    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 36px;
    }
  `;

  hass?: HomeAssistant;
  config?: GitHubInsightsCardConfig;
  definition!: CardDefinition;

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

  private toggleMetric(key: string, checked: boolean): void {
    const metrics = new Set(this.config?.metrics ?? []);
    if (checked) metrics.add(key);
    else metrics.delete(key);
    this.updateConfig({ metrics: [...metrics] });
  }

  protected render() {
    if (!this.config) return nothing;
    return html`
      <label>
        Title
        <input
          aria-label="Card title"
          .value=${this.config.title ?? ""}
          @input=${(event: Event) =>
            this.updateConfig({ title: (event.target as HTMLInputElement).value || undefined })}
        />
      </label>
      <label>
        Layout
        <select
          aria-label="Card layout"
          .value=${this.config.layout ?? this.definition.defaultLayout}
          @change=${(event: Event) =>
            this.updateConfig({
              layout: (event.target as HTMLSelectElement)
                .value as GitHubInsightsCardConfig["layout"],
            })}
        >
          ${["responsive", "compact", "hero", "gauges", "stacked", "list", "grid"].map(
            (layout) => html`<option value=${layout}>${layout}</option>`,
          )}
        </select>
      </label>
      ${this.definition.kind === "repository"
        ? html`<label>
            Repository
            <input
              aria-label="Repository full name"
              placeholder="owner/repository"
              .value=${this.config.repository ?? ""}
              @input=${(event: Event) =>
                this.updateConfig({ repository: (event.target as HTMLInputElement).value || undefined })}
            />
          </label>`
        : nothing}
      ${this.definition.kind === "repositories"
        ? html`
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
              Repository view
              <select
                aria-label="Repository view"
                .value=${this.config.view ?? "compact"}
                @change=${(event: Event) =>
                  this.updateConfig({
                    view: (event.target as HTMLSelectElement)
                      .value as GitHubInsightsCardConfig["view"],
                  })}
              >
                ${["compact", "expanded", "list", "grid"].map(
                  (view) => html`<option value=${view}>${view}</option>`,
                )}
              </select>
            </label>
          `
        : nothing}
      ${this.definition.kind === "compact"
        ? html`
            ${this.metricSelect("Primary metric", "primary_metric")}
            ${this.metricSelect("Secondary metric", "secondary_metric")}
          `
        : html`<fieldset class="metrics">
            <legend>Metrics</legend>
            ${Object.values(METRICS).map(
              (metric) => html`
                <label class="check">
                  <input
                    type="checkbox"
                    .checked=${this.config?.metrics?.includes(metric.key) ?? false}
                    @change=${(event: Event) =>
                      this.toggleMetric(
                        metric.key,
                        (event.target as HTMLInputElement).checked,
                      )}
                  />
                  ${metric.label}${metric.estimated ? " (estimated)" : ""}
                </label>
              `,
            )}
          </fieldset>`}
      <fieldset>
        <legend>Display options</legend>
        <label class="check">
          <input
            type="checkbox"
            .checked=${this.config.show_estimated_minutes ?? true}
            @change=${(event: Event) =>
              this.updateConfig({
                show_estimated_minutes: (event.target as HTMLInputElement).checked,
              })}
          />
          Show estimated equivalent minutes
        </label>
        <label class="check">
          <input
            type="checkbox"
            .checked=${this.config.show_forecast ?? true}
            @change=${(event: Event) =>
              this.updateConfig({ show_forecast: (event.target as HTMLInputElement).checked })}
          />
          Show forecast when supplied by GitHub Insights
        </label>
      </fieldset>
    `;
  }

  private metricSelect(
    label: string,
    key: "primary_metric" | "secondary_metric",
  ) {
    return html`<label>
      ${label}
      <select
        aria-label=${label}
        .value=${this.config?.[key] ?? ""}
        @change=${(event: Event) =>
          this.updateConfig({ [key]: (event.target as HTMLSelectElement).value })}
      >
        ${Object.values(METRICS).map(
          (metric) => html`<option value=${metric.key}>${metric.label}</option>`,
        )}
      </select>
    </label>`;
  }
}

export function createEditorClass(definition: CardDefinition) {
  return class extends GitHubInsightsEditor {
    definition = definition;
  };
}
