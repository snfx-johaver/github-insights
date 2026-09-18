import resolve from "@rollup/plugin-node-resolve";
import typescript from "@rollup/plugin-typescript";

export default {
  input: "src/index.ts",
  output: {
    file: "build/github-insights-cards.js",
    format: "es",
    sourcemap: false,
  },
  plugins: [resolve(), typescript()],
};

