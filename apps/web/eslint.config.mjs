import js from "@eslint/js";
import ts from "typescript-eslint";
import hooks from "eslint-plugin-react-hooks";
import { defineConfig, globalIgnores } from "eslint/config";
export default defineConfig([
  globalIgnores([
    ".next/**",
    ".next-e2e/**",
    ".next-verify/**",
    "test-results/**",
    "next-env.d.ts",
  ]),
  js.configs.recommended,
  ts.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    plugins: { "react-hooks": hooks },
    rules: {
      ...hooks.configs.recommended.rules,
      "no-empty": ["error", { allowEmptyCatch: true }],
    },
  },
]);
