export type CardKind =
  | "overview"
  | "usage"
  | "repositories"
  | "repository"
  | "actions"
  | "copilot"
  | "activity"
  | "contributions"
  | "security"
  | "compact"
  | "dashboard";

export type CardLayout =
  | "responsive"
  | "compact"
  | "hero"
  | "gauges"
  | "stacked"
  | "list"
  | "grid";

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
  title?: string;
  account?: string;
  entity?: string;
  entities?: Record<string, string>;
  repositories?: "auto" | string[];
  repository?: string;
  search?: string;
  group_by?: "none" | "organization" | "visibility" | "workflow_status";
  favorites?: string[];
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
  sections?: string[];
  metrics?: string[];
  layout?: CardLayout;
  view?: "compact" | "expanded" | "list" | "grid";
  period?: string;
  show_forecast?: boolean;
  show_archived?: boolean;
  show_forks?: boolean;
  show_estimated_minutes?: boolean;
  reference_runner?: string;
  primary_metric?: string;
  secondary_metric?: string;
  icon?: string;
  severity?: { green?: number; amber?: number; red?: number };
  tap_action?: CardAction;
  hold_action?: CardAction;
  double_tap_action?: CardAction;
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
  defaultLayout: CardLayout;
}
