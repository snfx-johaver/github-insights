export type CardKind = "insights" | "repository";

export type CardLayout =
  | "responsive"
  | "compact"
  | "expanded"
  | "detail";

export type InsightsPreset =
  | "overview"
  | "usage"
  | "actions"
  | "copilot"
  | "activity"
  | "contributions"
  | "security"
  | "dashboard"
  | "compact";

export type InsightsSection =
  | "overview"
  | "usage"
  | "actions"
  | "copilot"
  | "activity"
  | "contributions"
  | "security";

export interface CardAction {
  action?: "more-info" | "navigate" | "url" | "call-service" | "none";
  entity?: string;
  navigation_path?: string;
  url_path?: string;
  service?: string;
  service_data?: Record<string, unknown>;
}

export interface GitHubInsightsCardConfig {
  type: string;
  preset?: InsightsPreset;
  title?: string;
  account?: string;
  entity?: string;
  entities?: Record<string, string>;
  repositories?: "auto" | string[];
  repository?: string;
  search?: string;
  group_by?: "none" | "organization" | "visibility" | "workflow_status";
  favorites?: string[];
  repository_overrides?: Record<string, RepositoryDisplayOverride>;
  include?: {
    names?: string[];
    visibility?: string[];
  };
  exclude?: {
    names?: string[];
    archived?: boolean;
    forked?: boolean;
  };
  sort?: Array<{
    field: string;
    direction?: "ascending" | "descending";
    nulls?: "first" | "last";
  }>;
  sections?: InsightsSection[];
  metrics?: string[];
  layout?: CardLayout;
  view?: "compact" | "expanded" | "detail";
  period?: string;
  show_forecast?: boolean;
  show_archived?: boolean;
  show_forks?: boolean;
  show_estimated_minutes?: boolean;
  show_metric_badges?: boolean;
  show_debug?: boolean;
  metric_badges?: MetricBadgeConfig[];
  reference_runner?: string;
  primary_metric?: string;
  secondary_metric?: string;
  icon?: string;
  severity?: { green?: number; amber?: number; red?: number };
  tap_action?: CardAction;
  hold_action?: CardAction;
  double_tap_action?: CardAction;
}

export interface MetricBadgeConfig {
  attribute: string;
  icon?: string;
  label?: string;
}

export interface RepositoryDisplayOverride {
  title?: string;
  view?: "compact" | "expanded" | "detail";
  metrics?: string[];
  metric_badges?: MetricBadgeConfig[];
  favorite?: boolean;
}

export interface DiscoveredEntity {
  key: string;
  entityId: string;
  configEntryId?: string;
  deviceId?: string;
  repository?: string;
}

export interface CardDefinition {
  kind: CardKind;
  tag: string;
  editorTag: string;
  name: string;
  description: string;
  icon: string;
  defaultMetrics: string[];
  defaultSections: InsightsSection[];
  defaultLayout: CardLayout;
}
