import { beforeEach, describe, expect, it, vi } from "vitest";

import type { GitHubInsightsCardConfig } from "../src/models/config";
import type { HomeAssistant } from "../src/models/home-assistant";
import {
  entitiesByKey,
  EntityDiscoveryService,
} from "../src/services/entity-discovery";

const config: GitHubInsightsCardConfig = {
  type: "custom:github-insights-overview",
};

describe("entity discovery", () => {
  beforeEach(() => EntityDiscoveryService.clearCache());

  it("uses explicit metric mappings without registry access", async () => {
    const sendMessagePromise = vi.fn();
    const discovered = await EntityDiscoveryService.discover(
      {
        states: {},
        connection: { sendMessagePromise },
      },
      {
        ...config,
        entities: { actions_cost: "sensor.actions_cost" },
      },
    );

    expect(discovered).toEqual([
      { key: "actions_cost", entityId: "sensor.actions_cost" },
    ]);
    expect(sendMessagePromise).not.toHaveBeenCalled();
  });

  it("filters the entity registry by integration platform and uses translation keys", async () => {
    const sendMessagePromise = vi
      .fn()
      .mockResolvedValueOnce([
        {
          entity_id: "sensor.github_insights_account",
          platform: "github_insights",
          translation_key: "account",
          config_entry_id: "entry-1",
          device_id: "device-1",
          unique_id: "42_account",
          disabled_by: null,
        },
        {
          entity_id: "sensor.unrelated",
          platform: "other",
          translation_key: "account",
        },
      ])
      .mockResolvedValueOnce([
        { id: "device-1", name: "octocat/repository" },
      ]);
    const hass: HomeAssistant = {
      states: {},
      connection: { sendMessagePromise },
    };

    const discovered = await EntityDiscoveryService.discover(hass, config);

    expect(discovered).toEqual([
      {
        key: "account",
        entityId: "sensor.github_insights_account",
        configEntryId: "entry-1",
        deviceId: "device-1",
        repository: "octocat/repository",
      },
    ]);
    expect(entitiesByKey(discovered).get("account")?.entityId).toBe(
      "sensor.github_insights_account",
    );
  });

  it("tolerates a missing device registry capability", async () => {
    const sendMessagePromise = vi
      .fn()
      .mockResolvedValueOnce([
        {
          entity_id: "sensor.github_insights_account",
          platform: "github_insights",
          unique_id: "42_account",
        },
      ])
      .mockRejectedValueOnce(new Error("unsupported"));

    await expect(
      EntityDiscoveryService.discover(
        { states: {}, connection: { sendMessagePromise } },
        config,
      ),
    ).resolves.toEqual([
      {
        key: "account",
        entityId: "sensor.github_insights_account",
        configEntryId: undefined,
        deviceId: undefined,
        repository: undefined,
      },
    ]);
  });
});
