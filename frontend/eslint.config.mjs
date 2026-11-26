import { defineConfig } from "eslint/config";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import tseslint from "typescript-eslint";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig([
  // Generated from backend/openapi.yaml by `npm run gen:api`.
  { ignores: ["src/lib/api-schema.d.ts"] },
  {
    extends: [...nextCoreWebVitals],
  },
  {
    // Type-aware rules: catch unhandled promises (SWR mutate, async event
    // handlers) and `any` leaking out of untyped JSON.
    files: ["**/*.{ts,tsx}"],
    extends: [tseslint.configs.recommendedTypeChecked],
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: __dirname },
    },
  },
]);
