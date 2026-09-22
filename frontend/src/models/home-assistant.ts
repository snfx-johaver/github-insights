export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed?: string;
  last_updated?: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  language?: string;
  locale?: { language?: string };
  connection?: {
    sendMessagePromise<T>(message: Record<string, unknown>): Promise<T>;
  };
  callService?(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
  ): Promise<unknown>;
}

export interface EntityRegistryEntry {
  entity_id: string;
  platform?: string;
  config_entry_id?: string;
  device_id?: string;
  unique_id?: string;
  translation_key?: string;
  disabled_by?: string | null;
}

export interface DeviceRegistryEntry {
  id: string;
  config_entries?: string[];
  identifiers?: Array<[string, string]>;
  name?: string;
  name_by_user?: string | null;
  model?: string | null;
}
