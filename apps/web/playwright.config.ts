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
const webPort = Number(process.env.E2E_WEB_PORT || 3001);
const apiPort = Number(process.env.E2E_API_PORT || 8001);
if (
  ![webPort, apiPort].every(
    (port) => Number.isInteger(port) && port > 0 && port <= 65535,
  )
) {
  throw new Error("E2E_WEB_PORT and E2E_API_PORT must be valid TCP ports.");
}
const webOrigin = `http://localhost:${webPort}`;
const apiOrigin = `http://127.0.0.1:${apiPort}`;
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  use: {
    baseURL: webOrigin,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  reporter: "list",
  webServer: [
    {
      command: `"${python}" scripts/e2e_api.py`,
      cwd: root,
      url: `${apiOrigin}/api/health`,
      timeout: 60000,
      reuseExistingServer: false,
    },
    {
      command: `npx next dev --hostname 127.0.0.1 --port ${webPort}`,
      url: webOrigin,
      timeout: 90000,
      reuseExistingServer: false,
      env: { API_INTERNAL_URL: apiOrigin, NEXT_DIST_DIR: ".next-e2e" },
    },
  ],
});
