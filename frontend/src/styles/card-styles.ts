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
    --gi-ink: color-mix(in srgb, var(--primary-text-color) 92%, #ffffff);
    --gi-surface: color-mix(
      in srgb,
      var(--card-background-color) 88%,
      var(--primary-color)
    );
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

  .dashboard-card {
    position: relative;
    display: grid;
    gap: 18px;
    padding: 0 0 18px;
    background:
      radial-gradient(
        circle at 95% 0%,
        color-mix(in srgb, var(--primary-color) 15%, transparent),
        transparent 32%
      ),
      var(--card-background-color);
  }

  .dashboard-hero {
    position: relative;
    isolation: isolate;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    min-height: 132px;
    padding: 24px;
    overflow: hidden;
    color: var(--gi-ink);
    background:
      linear-gradient(
        135deg,
        color-mix(in srgb, var(--primary-color) 23%, var(--card-background-color)),
        color-mix(in srgb, #6e40c9 13%, var(--card-background-color)) 58%,
        var(--card-background-color)
      );
    border-bottom: 1px solid color-mix(in srgb, var(--primary-color) 20%, transparent);
  }

  .hero-glow {
    position: absolute;
    z-index: -1;
    width: 260px;
    height: 260px;
    top: -165px;
    right: -70px;
    border-radius: 50%;
    background: color-mix(in srgb, var(--primary-color) 38%, transparent);
    filter: blur(8px);
  }

  .hero-copy {
    display: grid;
    gap: 16px;
    min-width: 0;
  }

  .hero-title {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .hero-title img,
  .hero-mark {
    width: 52px;
    height: 52px;
    flex: 0 0 52px;
    border-radius: 16px;
    box-shadow: 0 10px 28px color-mix(in srgb, #000 22%, transparent);
  }

  .hero-title img {
    object-fit: cover;
  }

  .hero-mark {
    display: grid;
    place-items: center;
    color: #ffffff;
    background: color-mix(in srgb, var(--primary-color) 74%, #111827);
  }

  .hero-mark ha-icon {
    color: inherit;
    --mdc-icon-size: 30px;
  }

  .hero-title h2 {
    font-size: clamp(1.35rem, 4vw, 1.9rem);
    letter-spacing: -0.035em;
  }

  .hero-title p {
    margin: 4px 0 0;
    color: color-mix(in srgb, var(--primary-text-color) 72%, transparent);
    font-size: 0.9rem;
  }

  .eyebrow {
    color: color-mix(in srgb, var(--primary-color) 72%, var(--primary-text-color));
    font-size: 0.67rem;
    font-weight: 750;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }

  .health-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 7px 10px;
    border: 1px solid color-mix(in srgb, currentColor 28%, transparent);
    border-radius: 999px;
    background: color-mix(in srgb, currentColor 9%, var(--card-background-color));
    font-size: 0.73rem;
    font-weight: 700;
    white-space: nowrap;
  }

  .health-pill > span {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 0 4px color-mix(in srgb, currentColor 16%, transparent);
  }

  .health-pill.healthy {
    color: var(--gi-success);
  }

  .health-pill.warning {
    color: var(--gi-warning);
  }

  .health-pill.critical {
    color: var(--gi-critical);
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

  .dashboard-sections {
    display: grid;
    gap: 22px;
    padding: 0 18px;
  }

  .dashboard-section {
    display: grid;
    gap: 10px;
  }

  .section-heading,
  .section-title {
    display: flex;
    align-items: center;
  }

  .section-heading {
    justify-content: space-between;
    gap: 12px;
  }

  .section-title {
    gap: 8px;
  }

  .section-heading h3 {
    margin: 0;
    font-size: 0.92rem;
    font-weight: 700;
  }

  .section-title ha-icon {
    color: var(--primary-color);
    --mdc-icon-size: 18px;
  }

  .count {
    display: inline-grid;
    place-items: center;
    min-width: 26px;
    height: 26px;
    padding: 0 7px;
    border-radius: 999px;
    color: var(--secondary-text-color);
    background: var(--gi-soft);
    font-size: 0.72rem;
    font-weight: 700;
  }

  .dashboard-section .metric {
    position: relative;
    overflow: hidden;
    min-height: 112px;
    background:
      linear-gradient(
        145deg,
        color-mix(in srgb, var(--gi-soft) 86%, transparent),
        color-mix(in srgb, var(--card-background-color) 94%, transparent)
      );
    box-shadow: inset 0 1px color-mix(in srgb, #fff 8%, transparent);
  }

  .dashboard-section .metric::after {
    content: "";
    position: absolute;
    width: 74px;
    height: 74px;
    right: -38px;
    bottom: -46px;
    border-radius: 50%;
    background: color-mix(in srgb, var(--primary-color) 10%, transparent);
  }

  .dashboard-section .value {
    margin-top: 12px;
    font-size: clamp(1.2rem, 4vw, 1.65rem);
    letter-spacing: -0.035em;
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

  .dashboard-repositories {
    display: grid;
    gap: 10px;
    padding: 0 18px;
  }

  .dashboard-repositories .section-heading > div {
    display: grid;
    gap: 3px;
  }

  .repository-list {
    display: grid;
    gap: 8px;
  }

  .repository {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
  }

  .repository strong {
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .repository > ha-icon {
    --mdc-icon-size: 17px;
    color: var(--secondary-text-color);
  }

  .companion-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
    padding: 0 18px;
  }

  .companion-grid > * {
    min-width: 0;
  }

  .companion-grid mushroom-chips-card {
    padding: 2px 0;
  }

  .dashboard-card > .status {
    margin: 0 18px;
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

    .dashboard-card {
      padding: 0 0 14px;
    }

    .dashboard-hero {
      min-height: 118px;
      padding: 18px;
    }

    .dashboard-sections,
    .dashboard-repositories,
    .companion-grid {
      padding-inline: 12px;
    }

    .dashboard-card > .status {
      margin-inline: 12px;
    }

    .health-pill {
      padding: 6px 8px;
    }
  }

  @media (max-width: 360px) {
    .grid,
    :host([layout="compact"]) .grid {
      grid-template-columns: 1fr;
    }

    .dashboard-hero {
      display: grid;
      gap: 14px;
    }

    .health-pill {
      justify-self: start;
    }

    .repository {
      grid-template-columns: auto minmax(0, 1fr);
    }

    .repository .meta {
      display: none;
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
