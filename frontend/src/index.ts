import { CARD_DEFINITIONS } from "./cards/definitions";
import { createCardClass } from "./cards/github-insights-card";
import { createEditorClass } from "./editors/github-insights-editor";

declare global {
  interface Window {
    customCards?: Array<{
      type: string;
      name: string;
      description: string;
      preview?: boolean;
    }>;
  }
}

export const GITHUB_INSIGHTS_IMPLEMENTATION_PHASE = 8;
export { CARD_DEFINITIONS };
export * from "./models/config";
export * from "./models/home-assistant";
export * from "./models/metrics";
export * from "./services/entity-discovery";
export * from "./utilities/config";
export * from "./utilities/format";

for (const definition of CARD_DEFINITIONS) {
  if (!customElements.get(definition.editorTag)) {
    customElements.define(definition.editorTag, createEditorClass(definition));
  }
  if (!customElements.get(definition.tag)) {
    customElements.define(definition.tag, createCardClass(definition));
  }
}

window.customCards = window.customCards ?? [];
for (const definition of CARD_DEFINITIONS) {
  if (!window.customCards.some((card) => card.type === definition.tag)) {
    window.customCards.push({
      type: definition.tag,
      name: definition.name,
      description: definition.description,
      preview: true,
    });
  }
}

console.info(
  `%c GitHub Insights Cards %c ${CARD_DEFINITIONS.length} cards registered `,
  "color:white;background:#24292f;padding:3px 6px;border-radius:4px 0 0 4px",
  "color:#24292f;background:#58a6ff;padding:3px 6px;border-radius:0 4px 4px 0",
);
