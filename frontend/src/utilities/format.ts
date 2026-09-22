import type { HassEntity, HomeAssistant } from "../models/home-assistant";
import type { MetricDefinition } from "../models/metrics";

const UNKNOWN_STATES = new Set(["unknown", "unavailable", "none", "null", ""]);

export function entityAvailable(entity: HassEntity | undefined): boolean {
  return Boolean(entity && !UNKNOWN_STATES.has(entity.state.toLowerCase()));
}

export function numericState(entity: HassEntity | undefined): number | undefined {
  if (!entityAvailable(entity)) return undefined;
  const value = Number(entity?.state);
  return Number.isFinite(value) ? value : undefined;
}

export function formatMetric(
  hass: HomeAssistant | undefined,
  entity: HassEntity | undefined,
  definition: MetricDefinition,
): string {
  if (!entityAvailable(entity)) return "Unavailable";
  const locale = hass?.locale?.language ?? hass?.language ?? "en";
  const value = entity?.state ?? "";
  const numberValue = Number(value);
  const unit = String(entity?.attributes.unit_of_measurement ?? "");

  if (definition.format === "boolean") {
    return value === "on" || value === "true" ? "Yes" : "No";
  }
  if (definition.format === "datetime") {
    const date = new Date(value);
    return Number.isNaN(date.valueOf())
      ? value
      : new Intl.DateTimeFormat(locale, {
          dateStyle: "medium",
          timeStyle: "short",
        }).format(date);
  }
  if (Number.isFinite(numberValue)) {
    if (definition.format === "currency") {
      const currency = String(entity?.attributes.currency ?? unit ?? "USD");
      try {
        return new Intl.NumberFormat(locale, {
          style: "currency",
          currency,
          maximumFractionDigits: 2,
        }).format(numberValue);
      } catch {
        return `${numberValue.toLocaleString(locale)} ${currency}`.trim();
      }
    }
    const formatted = new Intl.NumberFormat(locale, {
      maximumFractionDigits: 2,
    }).format(numberValue);
    if (definition.format === "percent") return `${formatted}%`;
    return `${formatted}${unit ? ` ${unit}` : ""}`;
  }
  return value;
}

export function safeHttpUrl(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" || parsed.protocol === "http:"
      ? parsed.href
      : undefined;
  } catch {
    return undefined;
  }
}

export function safeHttpsUrl(value: unknown): string | undefined {
  const url = safeHttpUrl(value);
  return url?.startsWith("https:") ? url : undefined;
}

export function safeText(value: unknown, maximumLength = 160): string | undefined {
  if (
    typeof value !== "string" &&
    typeof value !== "number" &&
    typeof value !== "boolean"
  ) {
    return undefined;
  }
  const text = Array.from(String(value), (character) => {
    const code = character.charCodeAt(0);
    return code <= 31 || code === 127 ? " " : character;
  })
    .join("")
    .trim();
  return text ? text.slice(0, maximumLength) : undefined;
}

export function severityClass(
  value: number | undefined,
  severity: { amber?: number; red?: number } | undefined,
): string {
  if (value === undefined) return "neutral";
  if (value >= (severity?.red ?? 90)) return "critical";
  if (value >= (severity?.amber ?? 70)) return "warning";
  return "healthy";
}
