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
      "github-insights-usage-editor",
    ) as TestEditor;
    editor.setConfig({ type: "custom:github-insights-usage" });
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
      type: "custom:github-insights-usage",
      title: "Usage status",
      layout: "hero",
    });
  });
});
