import { defineConfig } from "@playwright/test";
import path from "node:path";
const root = path.resolve(__dirname, "../..");
const python =
  process.env.PYTHON_EXECUTABLE ||
  path.join(
    root,
    ".venv",
    process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
  );
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  use: {
    baseURL: "http://localhost:3001",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  reporter: "list",
  webServer: [
    {
      command: `"${python}" scripts/e2e_api.py`,
      cwd: root,
      url: "http://127.0.0.1:8001/api/health",
      timeout: 60000,
      reuseExistingServer: false,
    },
    {
      command: "npx next dev --hostname 127.0.0.1 --port 3001",
      url: "http://localhost:3001",
      timeout: 90000,
      reuseExistingServer: false,
      env: { API_INTERNAL_URL: "http://127.0.0.1:8001" },
    },
  ],
});
