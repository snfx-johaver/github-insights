import type {
  CardDefinition,
  InsightsPreset,
  InsightsSection,
} from "../models/config";

const definitions: CardDefinition[] = [
  {
    kind: "insights",
    tag: "github-insights-card",
    editorTag: "github-insights-card-editor",
    name: "GitHub Insights",
    description:
      "Configurable account, usage, Actions, Copilot, activity, contributions, and security insights.",
    icon: "mdi:github",
    defaultMetrics: [
      "account",
      "actions_configured_included_minutes",
      "actions_configured_minutes_used_percent",
      "actions_configured_minutes_remaining",
      "actions_gross_cost",
      "actions_discount",
      "actions_cost",
      "actions_budget_percent",
      "copilot_paid_usage",
      "public_repositories",
      "open_pull_requests",
      "workflow_health",
      "dependabot_alerts",
      "commits",
      "contributions",
      "last_successful_sync",
    ],
    defaultSections: [
      "overview",
      "usage",
      "actions",
      "copilot",
      "activity",
      "contributions",
      "security",
    ],
    defaultLayout: "expanded",
  },
  {
    kind: "repository",
    tag: "github-insights-repository-card",
    editorTag: "github-insights-repository-card-editor",
    name: "GitHub Insights repository",
    description:
      "Configurable collection or detail view for discovered repositories.",
    icon: "mdi:source-repository-multiple",
    defaultMetrics: [
      "stars",
      "forks",
      "open_issues",
      "open_pull_requests",
      "workflow_health",
      "actions_usage_percent",
    ],
    defaultSections: [],
    defaultLayout: "responsive",
  },
];

export const CARD_DEFINITIONS = definitions;

export const INSIGHTS_SECTIONS: InsightsSection[] = [
  "overview",
  "usage",
  "actions",
  "copilot",
  "activity",
  "contributions",
  "security",
];

export const PRESET_CONFIGS: Record<
  InsightsPreset,
  {
    metrics: string[];
    sections: InsightsSection[];
    layout: CardDefinition["defaultLayout"];
  }
> = {
  overview: {
    metrics: [
      "account",
      "actions_configured_minutes_used_percent",
      "actions_configured_minutes_remaining",
      "actions_cost",
      "copilot_paid_usage",
      "public_repositories",
      "open_pull_requests",
      "workflow_health",
      "dependabot_alerts",
      "last_successful_sync",
    ],
    sections: ["overview", "usage", "actions", "copilot", "security"],
    layout: "responsive",
  },
  usage: {
    metrics: [
      "actions_configured_included_minutes",
      "actions_configured_minutes_used",
      "actions_configured_minutes_remaining",
      "actions_configured_minutes_used_percent",
      "actions_gross_cost",
      "actions_discount",
      "actions_cost",
      "actions_discounted_usage",
      "actions_billable_usage",
      "actions_budget",
      "actions_budget_remaining",
      "actions_budget_percent",
      "actions_blocked",
      "actions_estimated_minutes_remaining",
      "billing_period",
      "copilot_paid_usage",
    ],
    sections: ["usage", "actions", "copilot"],
    layout: "expanded",
  },
  actions: {
    metrics: [
      "actions_configured_included_minutes",
      "actions_configured_minutes_used",
      "actions_configured_minutes_remaining",
      "actions_configured_minutes_used_percent",
      "actions_gross_cost",
      "actions_discount",
      "actions_cost",
      "workflow_health",
      "actions_discounted_usage",
      "actions_billable_usage",
      "actions_budget",
      "actions_budget_remaining",
      "actions_budget_percent",
      "actions_blocked",
      "actions_estimated_minutes_remaining",
      "billing_period",
    ],
    sections: ["usage", "actions"],
    layout: "responsive",
  },
  copilot: {
    metrics: [
      "copilot_paid_usage",
      "copilot_cost",
      "copilot_active_users",
      "last_successful_sync",
    ],
    sections: ["copilot", "overview"],
    layout: "responsive",
  },
  activity: {
    metrics: [
      "commits",
      "pull_requests_opened",
      "pull_requests_merged",
      "issues_opened",
      "reviews",
      "releases",
    ],
    sections: ["activity"],
    layout: "responsive",
  },
  contributions: {
    metrics: ["contributions", "current_streak", "longest_streak"],
    sections: ["contributions"],
    layout: "responsive",
  },
  security: {
    metrics: [
      "dependabot_alerts",
      "code_scanning_alerts",
      "secret_scanning_alerts",
      "last_successful_sync",
    ],
    sections: ["security", "overview"],
    layout: "responsive",
  },
  dashboard: {
    metrics: definitions[0].defaultMetrics,
    sections: definitions[0].defaultSections,
    layout: "expanded",
  },
  compact: {
    metrics: [
      "actions_configured_minutes_used_percent",
      "actions_budget_remaining",
    ],
    sections: ["usage", "actions"],
    layout: "compact",
  },
};

export function definitionForTag(tag: string): CardDefinition {
  const definition = definitions.find((candidate) => candidate.tag === tag);
  if (!definition) throw new Error(`Unknown GitHub Insights card: ${tag}`);
  return definition;
}
