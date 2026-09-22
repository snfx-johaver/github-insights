import type {
  CardDefinition,
  GitHubInsightsCardConfig,
} from "../models/config";

export function normalizeConfig(
  value: GitHubInsightsCardConfig,
  definition: CardDefinition,
): GitHubInsightsCardConfig {
  if (!value || typeof value !== "object") {
    throw new Error("GitHub Insights card configuration is required.");
  }
  if (value.type && value.type !== `custom:${definition.tag}`) {
    throw new Error(`Expected type custom:${definition.tag}.`);
  }
  return {
    type: `custom:${definition.tag}`,
    title: value.title,
    account: value.account,
    entity: value.entity,
    entities: { ...(value.entities ?? {}) },
    repositories: value.repositories ?? "auto",
    repository: value.repository,
    search: value.search,
    group_by: value.group_by ?? "none",
    favorites: [...(value.favorites ?? [])],
    include: {
      names: [...(value.include?.names ?? [])],
      visibility: [...(value.include?.visibility ?? [])],
    },
    exclude: {
      names: [...(value.exclude?.names ?? [])],
      archived: value.exclude?.archived ?? !value.show_archived,
      forked: value.exclude?.forked ?? false,
    },
    sort: (value.sort ?? [
      { field: "name", direction: "ascending", nulls: "last" },
    ]).map((sort) => ({ ...sort })),
    sections: [...(value.sections ?? [])],
    metrics: [...(value.metrics ?? definition.defaultMetrics)],
    layout: value.layout ?? definition.defaultLayout,
    view: value.view ?? "compact",
    period: value.period ?? "current_billing_cycle",
    show_forecast: value.show_forecast ?? true,
    show_archived: value.show_archived ?? false,
    show_forks: value.show_forks ?? true,
    show_estimated_minutes: value.show_estimated_minutes ?? true,
    reference_runner: value.reference_runner ?? "linux_standard",
    primary_metric: value.primary_metric ?? definition.defaultMetrics[0],
    secondary_metric: value.secondary_metric ?? definition.defaultMetrics[1],
    icon: value.icon ?? definition.icon,
    severity: {
      green: value.severity?.green ?? 0,
      amber: value.severity?.amber ?? 70,
      red: value.severity?.red ?? 90,
    },
    tap_action: value.tap_action,
    hold_action: value.hold_action,
    double_tap_action: value.double_tap_action,
  };
}

export function stubConfig(definition: CardDefinition): GitHubInsightsCardConfig {
  return normalizeConfig({ type: `custom:${definition.tag}` }, definition);
}
