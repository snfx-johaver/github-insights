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

  .metric-heading {
    gap: 7px;
    min-height: 24px;
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
  }

  .repository {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px;
  }

  .repository strong {
    overflow: hidden;
    text-overflow: ellipsis;
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
  a:focus-visible {
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
    :host([layout="compact"]) .grid {
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
