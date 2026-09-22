import { css } from "lit";

export const cardStyles = css`
  :host {
    display: block;
    color: var(--primary-text-color);
    --gi-gap: 12px;
    --gi-soft: color-mix(in srgb, var(--primary-color) 11%, transparent);
    --gi-warning: var(--warning-color, #f59e0b);
    --gi-critical: var(--error-color, #db4437);
    --gi-success: var(--success-color, #43a047);
  }

  ha-card {
    overflow: hidden;
    border-radius: var(--ha-card-border-radius, 16px);
    box-shadow: var(--ha-card-box-shadow);
    background: var(--card-background-color);
  }

  .card {
    padding: 16px;
  }

  .header,
  .account,
  .metric-heading,
  .status,
  .actions {
    display: flex;
    align-items: center;
  }

  .header {
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
  }

  h2 {
    margin: 0;
    font-size: 1.15rem;
    line-height: 1.35;
  }

  .subtitle,
  .label,
  .meta,
  .empty {
    color: var(--secondary-text-color);
  }

  .account {
    gap: 10px;
    min-width: 0;
  }

  .account img {
    flex: 0 0 auto;
    border-radius: 50%;
  }

  .subtitle,
  .meta {
    font-size: 0.78rem;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(145px, 100%), 1fr));
    gap: var(--gi-gap);
  }

  :host([layout="compact"]) .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .metric,
  .module,
  .repository {
    min-width: 0;
    padding: 12px;
    border-radius: calc(var(--ha-card-border-radius, 16px) * 0.72);
    background: var(--gi-soft);
    border: 1px solid color-mix(in srgb, var(--divider-color) 68%, transparent);
  }

  .metric.prominent {
    border-color: color-mix(in srgb, var(--primary-color) 45%, var(--divider-color));
    background: color-mix(in srgb, var(--primary-color) 15%, var(--card-background-color));
  }

  .metric-heading {
    gap: 7px;
    min-height: 24px;
  }

  .metric-link,
  .repository a {
    color: var(--primary-text-color);
    font-weight: 650;
    text-decoration-thickness: 1px;
    text-underline-offset: 3px;
  }

  ha-icon {
    color: var(--state-icon-color, var(--primary-color));
    --mdc-icon-size: 20px;
  }

  .value {
    display: block;
    margin-top: 7px;
    font-size: 1.25rem;
    font-weight: 650;
    overflow-wrap: anywhere;
  }

  .metric.warning {
    --gi-soft: color-mix(in srgb, var(--gi-warning) 14%, transparent);
  }

  .metric.critical {
    --gi-soft: color-mix(in srgb, var(--gi-critical) 16%, transparent);
  }

  .metric.healthy {
    --gi-soft: color-mix(in srgb, var(--gi-success) 11%, transparent);
  }

  .metric.unavailable {
    opacity: 0.72;
  }

  .bar {
    height: 6px;
    margin-top: 10px;
    overflow: hidden;
    border-radius: 999px;
    background: color-mix(in srgb, var(--divider-color) 70%, transparent);
  }

  .bar > span {
    display: block;
    height: 100%;
    width: var(--progress, 0%);
    max-width: 100%;
    border-radius: inherit;
    background: var(--primary-color);
    transition: width 180ms ease-out;
  }

  svg {
    display: block;
    width: 100%;
    height: 32px;
    margin-top: 8px;
    color: var(--primary-color);
  }

  .status {
    gap: 8px;
    padding: 12px;
    border-radius: 12px;
    background: color-mix(in srgb, var(--divider-color) 35%, transparent);
  }

  .status.error,
  .status.blocked {
    background: color-mix(in srgb, var(--gi-critical) 15%, transparent);
  }

  .status.warning {
    background: color-mix(in srgb, var(--gi-warning) 15%, transparent);
  }

  .repositories {
    display: grid;
    gap: 8px;
    margin-top: 12px;
  }

  .repository {
    display: block;
    gap: 8px;
  }

  .repository-heading {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
  }

  .repository-heading strong,
  .repository-heading a {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .favorite {
    width: 1em;
    color: var(--warning-color, #f5b301);
  }

  .repository-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(130px, 100%), 1fr));
    gap: 8px;
    margin-top: 10px;
  }

  .repository.compact .repository-metrics {
    display: flex;
    overflow-x: auto;
    padding-bottom: 2px;
    scrollbar-width: thin;
  }

  .repository.compact .metric {
    flex: 1 0 120px;
    padding: 9px;
  }

  .repository.compact .metric .meta,
  .repository.compact .metric svg {
    display: none;
  }

  .badges {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 8px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    min-width: 0;
    padding: 3px 7px;
    border-radius: 999px;
    font-size: 0.7rem;
    color: var(--secondary-text-color);
    background: color-mix(in srgb, var(--divider-color) 50%, transparent);
  }

  .badge ha-icon {
    --mdc-icon-size: 14px;
  }

  .badge-label {
    font-weight: 650;
  }

  .diagnostics {
    margin-top: 12px;
    border-top: 1px solid var(--divider-color);
    padding-top: 12px;
  }

  .diagnostics pre {
    max-height: 260px;
    overflow: auto;
    padding: 10px;
    border-radius: 8px;
    color: var(--primary-text-color);
    background: color-mix(in srgb, var(--divider-color) 35%, transparent);
    font: 0.75rem/1.45 ui-monospace, SFMono-Regular, Consolas, monospace;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }

  .heatmap {
    display: grid;
    grid-template-columns: repeat(13, 1fr);
    gap: 3px;
    margin-top: 12px;
  }

  .heatmap span {
    aspect-ratio: 1;
    min-width: 5px;
    border-radius: 2px;
    background: color-mix(
      in srgb,
      var(--primary-color) calc(var(--intensity) * 22%),
      var(--divider-color)
    );
  }

  button,
  a {
    min-height: 40px;
    min-width: 40px;
  }

  button {
    border: 0;
    border-radius: 999px;
    padding: 0 14px;
    color: var(--primary-text-color);
    background: var(--gi-soft);
    cursor: pointer;
  }

  button:focus-visible,
  a:focus-visible,
  ha-card:focus-visible,
  pre:focus-visible {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  @media (max-width: 520px) {
    .card {
      padding: 12px;
    }

    .grid,
    :host([layout="compact"]) .grid,
    .repository-metrics {
      grid-template-columns: 1fr 1fr;
    }
  }

  @media (max-width: 360px) {
    .grid,
    :host([layout="compact"]) .grid {
      grid-template-columns: 1fr;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      scroll-behavior: auto !important;
      transition-duration: 0.001ms !important;
      animation-duration: 0.001ms !important;
      animation-iteration-count: 1 !important;
    }
  }
`;
