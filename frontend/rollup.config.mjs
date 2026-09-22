import resolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";

export default {
  input: "src/index.ts",
  output: {
    file: "../custom_components/github_insights/frontend/github-insights-cards.js",
    format: "es",
    sourcemap: false,
    generatedCode: "es2015",
  },
  plugins: [resolve(), typescript()],
};
