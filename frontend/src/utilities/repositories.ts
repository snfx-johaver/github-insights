import type {
  DiscoveredEntity,
  GitHubInsightsCardConfig,
  RepositoryDisplayOverride,
} from "../models/config";
import type { HassEntity, HomeAssistant } from "../models/home-assistant";

const UNAVAILABLE_STATES = new Set(["unknown", "unavailable", "none", "null", ""]);

export interface RepositoryModel {
  name: string;
  title: string;
  favorite: boolean;
  entities: Map<string, HassEntity>;
  override?: RepositoryDisplayOverride;
}

function comparable(value: unknown): number | string | undefined {
  if (typeof value === "number") return Number.isFinite(value) ? value : undefined;
  if (typeof value !== "string" || !value.trim()) return undefined;
  if (UNAVAILABLE_STATES.has(value.trim().toLocaleLowerCase())) return undefined;
  const numeric = Number(value);
  if (Number.isFinite(numeric)) return numeric;
  const timestamp = Date.parse(value);
  return Number.isNaN(timestamp) ? value.toLocaleLowerCase() : timestamp;
}

function compareValues(
  left: unknown,
  right: unknown,
  direction: "ascending" | "descending",
  nulls: "first" | "last",
): number {
  const a = comparable(left);
  const b = comparable(right);
  if (a === undefined || b === undefined) {
    if (a === b) return 0;
    return (a === undefined ? 1 : -1) * (nulls === "last" ? 1 : -1);
  }
  const result =
    typeof a === "number" && typeof b === "number"
      ? a - b
      : String(a).localeCompare(String(b));
  return direction === "descending" ? -result : result;
}

function sortValue(repository: RepositoryModel, field: string): unknown {
  if (field === "name") return repository.name;
  if (field === "favorite") return repository.favorite ? 1 : 0;
  const entity = repository.entities.get(field);
  return entity?.state ?? entity?.attributes[field];
}

function repositoryAttribute(
  entities: Map<string, HassEntity>,
  attribute: string,
): unknown {
  for (const entity of entities.values()) {
    if (attribute in entity.attributes) return entity.attributes[attribute];
  }
  return undefined;
}

export function buildRepositories(
  discovered: DiscoveredEntity[],
  hass: HomeAssistant | undefined,
  config: GitHubInsightsCardConfig,
): RepositoryModel[] {
  const selected =
    config.repositories === "auto" ? undefined : new Set(config.repositories ?? []);
  const included = new Set(config.include?.names ?? []);
  const includedVisibility = new Set(config.include?.visibility ?? []);
  const excluded = new Set(config.exclude?.names ?? []);
  const favorites = new Set(config.favorites ?? []);
  const search = config.search?.trim().toLocaleLowerCase();
  const grouped = new Map<string, Map<string, HassEntity>>();

  for (const reference of discovered) {
    if (!reference.repository) continue;
    if (selected && !selected.has(reference.repository)) continue;
    const entity = hass?.states[reference.entityId];
    if (!entity) continue;
    const entities = grouped.get(reference.repository) ?? new Map<string, HassEntity>();
    entities.set(reference.key, entity);
    grouped.set(reference.repository, entities);
  }

  const repositories = [...grouped.entries()]
    .filter(([name]) => !search || name.toLocaleLowerCase().includes(search))
    .filter(([name]) => included.size === 0 || included.has(name))
    .filter(([name]) => !excluded.has(name))
    .filter(([, entities]) => {
      const visibility = repositoryAttribute(entities, "visibility");
      return (
        includedVisibility.size === 0 ||
        (typeof visibility === "string" && includedVisibility.has(visibility))
      );
    })
    .filter(([, entities]) => {
      const archived = repositoryAttribute(entities, "archived") === true;
      return !(config.exclude?.archived ?? !config.show_archived) || !archived;
    })
    .filter(([, entities]) => {
      const fork = repositoryAttribute(entities, "fork") === true;
      return !(config.exclude?.forked ?? config.show_forks === false) || !fork;
    })
    .map(([name, entities]) => {
      const override = config.repository_overrides?.[name];
      return {
        name,
        title: override?.title ?? name,
        favorite: override?.favorite ?? favorites.has(name),
        entities,
        override,
      };
    });

  const sorts = config.sort ?? [];
  return repositories.sort((a, b) => {
    const favoriteDifference = Number(b.favorite) - Number(a.favorite);
    if (favoriteDifference) return favoriteDifference;
    for (const sort of sorts) {
      const difference = compareValues(
        sortValue(a, sort.field),
        sortValue(b, sort.field),
        sort.direction ?? "ascending",
        sort.nulls ?? "last",
      );
      if (difference) return difference;
    }
    return a.name.localeCompare(b.name);
  });
}
