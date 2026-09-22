import { describe, expect, it } from "vitest";

import type { GitHubInsightsCardConfig } from "../src/index";
import { CARD_DEFINITIONS } from "../src/index";

interface TestEditor extends HTMLElement {
  setConfig(config: GitHubInsightsCardConfig): void;
  updateComplete: Promise<boolean>;
}

describe("visual editors", () => {
  it("creates an editor for every card and emits normalized changes", async () => {
    for (const definition of CARD_DEFINITIONS) {
      const editor = document.createElement(definition.editorTag) as TestEditor;
      editor.setConfig({ type: `custom:${definition.tag}` });
      document.body.append(editor);
      await editor.updateComplete;
      expect(editor.shadowRoot?.querySelector('[aria-label="Card title"]')).not
        .toBeNull();
    }

    const editor = document.createElement(
      "github-insights-card-editor",
    ) as TestEditor;
    editor.setConfig({
      type: "custom:github-insights-card",
      preset: "usage",
    });
    document.body.append(editor);
    await editor.updateComplete;
    const changed = new Promise<GitHubInsightsCardConfig>((resolve) => {
      editor.addEventListener("config-changed", (event) => {
        resolve((event as CustomEvent).detail.config);
      });
    });
    const title = editor.shadowRoot?.querySelector(
      '[aria-label="Card title"]',
    ) as HTMLInputElement;
    title.value = "Usage status";
    title.dispatchEvent(new Event("input"));

    await expect(changed).resolves.toMatchObject({
      type: "custom:github-insights-card",
      title: "Usage status",
      layout: "expanded",
    });
  });

  it("exposes section, metric ordering, and repository configuration controls", async () => {
    const insights = document.createElement(
      "github-insights-card-editor",
    ) as TestEditor;
    insights.setConfig({ type: "custom:github-insights-card" });
    document.body.append(insights);
    await insights.updateComplete;
    expect(insights.shadowRoot?.querySelector('[aria-label="Card preset"]')).toBeTruthy();
    expect(insights.shadowRoot?.querySelector('[aria-label="Move overview down"]')).toBeTruthy();
    expect(insights.shadowRoot?.querySelector('[aria-label^="Move Account"]')).toBeTruthy();

    const repositories = document.createElement(
      "github-insights-repository-card-editor",
    ) as TestEditor;
    repositories.setConfig({
      type: "custom:github-insights-repository-card",
    });
    document.body.append(repositories);
    await repositories.updateComplete;
    expect(repositories.shadowRoot?.querySelector('[aria-label="Repository selection"]')).toBeTruthy();
    expect(repositories.shadowRoot?.querySelector('[aria-label="Primary repository sort"]')).toBeTruthy();
    expect(repositories.shadowRoot?.querySelector('[aria-label="Repository overrides"]')).toBeTruthy();
  });
});
