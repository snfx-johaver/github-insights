export type MetricFormat =
  | "number"
  | "percent"
  | "currency"
  | "duration"
  | "datetime"
  | "text"
  | "boolean";

export interface MetricDefinition {
  key: string;
  label: string;
  icon: string;
  format: MetricFormat;
  estimated?: boolean;
  sourceLabel?: string;
  prominent?: boolean;
  group:
    | "account"
    | "actions"
    | "billing"
    | "copilot"
    | "repositories"
    | "activity"
    | "security"
    | "diagnostic";
}

const metric = (
  key: string,
  label: string,
  icon: string,
  format: MetricFormat,
  group: MetricDefinition["group"],
  estimated = false,
  sourceLabel?: string,
  prominent = false,
): MetricDefinition => ({
  key,
  label,
  icon,
  format,
  group,
  estimated,
  sourceLabel,
  prominent,
});

export const METRICS: Record<string, MetricDefinition> = Object.fromEntries(
  [
    metric("account", "Account", "mdi:github", "text", "account"),
    metric("public_repositories", "Public repositories", "mdi:source-repository", "number", "repositories"),
    metric("private_repositories", "Private repositories", "mdi:lock", "number", "repositories"),
    metric("repositories", "Repositories", "mdi:source-repository-multiple", "number", "repositories"),
    metric("stars", "Stars", "mdi:star-outline", "number", "repositories"),
    metric("forks", "Forks", "mdi:source-fork", "number", "repositories"),
    metric("open_issues", "Open issues", "mdi:alert-circle-outline", "number", "repositories"),
    metric("open_pull_requests", "Open pull requests", "mdi:source-pull", "number", "repositories"),
    metric("latest_commit", "Latest commit", "mdi:source-commit", "text", "repositories"),
    metric("latest_release", "Latest release", "mdi:tag-outline", "text", "repositories"),
    metric("last_push", "Last push", "mdi:clock-outline", "datetime", "repositories"),
    metric("traffic_views", "Traffic views", "mdi:eye-outline", "number", "repositories"),
    metric("workflow_health", "Workflow health", "mdi:check-circle-outline", "text", "actions"),
    metric("actions_runtime", "Workflow runtime", "mdi:timer-outline", "duration", "actions"),
    metric("actions_discounted_usage", "Discounted or included consumption", "mdi:package-variant", "number", "actions"),
    metric("actions_billable_usage", "Paid usage", "mdi:cash-plus", "number", "actions"),
    metric("actions_minutes_remaining", "Actions remaining", "mdi:timer-sand", "number", "actions"),
    metric("actions_usage_percent", "Actions usage", "mdi:gauge", "percent", "actions"),
    metric("actions_configured_included_minutes", "Configured allowance", "mdi:timer-check-outline", "number", "actions", false, "Configured GitHub Actions allowance", true),
    metric("actions_configured_minutes_used", "Allowance used", "mdi:timer-play-outline", "number", "actions", false, "Configured allowance calculation", true),
    metric("actions_configured_minutes_remaining", "Allowance remaining", "mdi:timer-sand", "number", "actions", false, "Configured allowance calculation", true),
    metric("actions_configured_minutes_used_percent", "Allowance used", "mdi:gauge", "percent", "actions", false, "Configured allowance calculation", true),
    metric("actions_cost", "Net cost", "mdi:cash", "currency", "billing", false, "Authoritative GitHub billing", true),
    metric("actions_gross_cost", "Gross cost", "mdi:cash-multiple", "currency", "billing", false, "Authoritative GitHub billing", true),
    metric("actions_discount", "Discount", "mdi:sale", "currency", "billing", false, "Authoritative GitHub billing", true),
    metric("actions_budget", "GitHub-enforced budget", "mdi:shield-lock", "currency", "billing"),
    metric("actions_budget_remaining", "Budget remaining", "mdi:piggy-bank-outline", "currency", "billing"),
    metric("actions_budget_percent", "Budget utilization", "mdi:chart-donut", "percent", "billing"),
    metric("actions_budget_scope", "Budget scope", "mdi:target-account", "text", "billing"),
    metric("billing_period", "Billing period", "mdi:calendar-range", "text", "billing"),
    metric("actions_estimated_minutes_remaining", "Estimated equivalent minutes", "mdi:calculator-variant-outline", "number", "billing", true),
    metric("actions_stop_usage", "Stop usage enabled", "mdi:stop-circle-outline", "boolean", "billing"),
    metric("actions_budget_warning", "Budget warning", "mdi:alert-outline", "boolean", "billing"),
    metric("actions_budget_exhausted", "Budget exhausted", "mdi:alert-octagon-outline", "boolean", "billing"),
    metric("actions_blocked", "Actions blocked", "mdi:block-helper", "boolean", "billing"),
    metric("actions_failed_runs", "Failed runs", "mdi:close-circle-outline", "number", "actions"),
    metric("actions_recent_runs", "Recent runs", "mdi:history", "number", "actions"),
    metric("actions_forecast", "Actions forecast", "mdi:chart-line", "currency", "billing"),
    metric("artifact_storage", "Artifact storage", "mdi:archive-outline", "number", "billing"),
    metric("package_storage", "Package storage", "mdi:package-variant", "number", "billing"),
    metric("cache_usage", "Cache usage", "mdi:cached", "number", "billing"),
    metric("copilot_usage_percent", "AI usage", "mdi:robot-outline", "percent", "copilot"),
    metric("copilot_included_quantity", "Included AI usage", "mdi:package-variant-closed", "number", "copilot"),
    metric("copilot_paid_usage", "Paid AI usage", "mdi:cash-plus", "number", "copilot"),
    metric("copilot_remaining_quantity", "AI usage remaining", "mdi:counter", "number", "copilot"),
    metric("copilot_cost", "AI cost", "mdi:cash", "currency", "copilot"),
    metric("copilot_active_users", "Active Copilot users", "mdi:account-group-outline", "number", "copilot"),
    metric("commits", "Commits", "mdi:source-commit", "number", "activity"),
    metric("pull_requests_opened", "Pull requests opened", "mdi:source-pull", "number", "activity"),
    metric("pull_requests_merged", "Pull requests merged", "mdi:source-merge", "number", "activity"),
    metric("issues_opened", "Issues opened", "mdi:alert-circle-outline", "number", "activity"),
    metric("reviews", "Reviews", "mdi:comment-check-outline", "number", "activity"),
    metric("releases", "Releases", "mdi:tag-outline", "number", "activity"),
    metric("contributions", "Contributions", "mdi:chart-timeline-variant-shimmer", "number", "activity"),
    metric("current_streak", "Current reliable streak", "mdi:fire", "number", "activity"),
    metric("longest_streak", "Longest reliable streak", "mdi:trophy-outline", "number", "activity"),
    metric("dependabot_alerts", "Dependabot alerts", "mdi:robot-angry-outline", "number", "security"),
    metric("code_scanning_alerts", "Code scanning alerts", "mdi:shield-search", "number", "security"),
    metric("secret_scanning_alerts", "Secret scanning alerts", "mdi:key-alert-outline", "number", "security"),
    metric("api_rate_limit_remaining", "API requests remaining", "mdi:speedometer", "number", "diagnostic"),
    metric("last_successful_sync", "API freshness", "mdi:clock-check-outline", "datetime", "diagnostic"),
  ].map((entry) => [entry.key, entry]),
);

export function metricDefinition(key: string): MetricDefinition {
  return (
    METRICS[key] ?? {
      key,
      label: key.replaceAll("_", " ").replace(/^\w/, (value) => value.toUpperCase()),
      icon: "mdi:chart-box-outline",
      format: "text",
      group: "diagnostic",
    }
  );
}
