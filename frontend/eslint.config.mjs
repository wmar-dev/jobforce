import { defineConfig } from "eslint/config";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
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
]);