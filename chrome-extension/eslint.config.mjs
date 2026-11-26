import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import globals from "globals";

export default defineConfig([
  { ignores: ["node_modules/", "coverage/"] },
  js.configs.recommended,
  {
    // Extension scripts: classic (non-module) scripts in the browser with the
    // chrome.* API. content.js also guards a CommonJS export for Jest.
    files: ["*.js"],
    languageOptions: {
      sourceType: "script",
      globals: { ...globals.browser, ...globals.webextensions, module: "readonly" },
    },
  },
  {
    files: ["tests/**/*.js"],
    languageOptions: {
      sourceType: "commonjs",
      globals: { ...globals.browser, ...globals.node, ...globals.jest },
    },
  },
]);
