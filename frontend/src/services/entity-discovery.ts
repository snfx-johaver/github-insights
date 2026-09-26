import type { GitHubInsightsCardConfig } from "../models/config";
import type { DiscoveredEntity } from "../models/config";
import type {
  DeviceRegistryEntry,
  EntityRegistryEntry,
  HomeAssistant,
} from "../models/home-assistant";
import { METRICS } from "../models/metrics";

const DOMAIN = "github_insights";

function keyFromEntry(entry: EntityRegistryEntry): string {
  if (entry.translation_key) return entry.translation_key;
  const unique = entry.unique_id ?? "";
  const knownKey = Object.keys(METRICS)
    .sort((a, b) => b.length - a.length)
    .find((key) => unique === key || unique.endsWith(`_${key}`));
  if (knownKey) return knownKey;
  const separator = unique.indexOf("_");
  return separator >= 0 ? unique.slice(separator + 1) : unique;
}

export class EntityDiscoveryService {
  private static cache = new WeakMap<object, Promise<DiscoveredEntity[]>>();

  static clearCache(): void {
    this.cache = new WeakMap<object, Promise<DiscoveredEntity[]>>();
  }

  static async discover(
    hass: HomeAssistant,
    config: GitHubInsightsCardConfig,
  ): Promise<DiscoveredEntity[]> {
    const explicit = Object.entries(config.entities ?? {}).map(
      ([key, entityId]) => ({ key, entityId }),
    );
    if (config.entity) {
      explicit.push({
        key: config.primary_metric ?? "primary",
        entityId: config.entity,
      });
    }
    if (explicit.length > 0) return explicit;
    if (!hass.connection) return [];

    const connection = hass.connection as object;
    let pending = this.cache.get(connection);
    if (!pending) {
      pending = this.load(hass);
      this.cache.set(connection, pending);
    }
    return pending;
  }

  private static async load(hass: HomeAssistant): Promise<DiscoveredEntity[]> {
    const connection = hass.connection;
    if (!connection) return [];
    const [entities, devices] = await Promise.all([
      connection.sendMessagePromise<EntityRegistryEntry[]>({
        type: "config/entity_registry/list",
      }),
      connection
        .sendMessagePromise<DeviceRegistryEntry[]>({
          type: "config/device_registry/list",
        })
        .catch(() => []),
    ]);
    const deviceNames = new Map(
      devices.map((device) => [
        device.id,
        device.name_by_user ?? device.name ?? undefined,
      ]),
    );

    return entities
      .filter(
        (entry) =>
          entry.platform === DOMAIN &&
          entry.disabled_by !== "integration" &&
          Boolean(entry.entity_id),
      )
      .map((entry) => ({
        key: keyFromEntry(entry),
        entityId: entry.entity_id,
        configEntryId: entry.config_entry_id,
        deviceId: entry.device_id,
        repository: entry.device_id
          ? deviceNames.get(entry.device_id)
          : undefined,
      }));
  }
}

export function entitiesByKey(
  discovered: DiscoveredEntity[],
): Map<string, DiscoveredEntity> {
  const result = new Map<string, DiscoveredEntity>();
  for (const entity of discovered) {
    if (!result.has(entity.key)) result.set(entity.key, entity);
  }
  return result;
}
