import type { NextConfig } from "next";

const apiOrigin = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
if (process.env.VERCEL) {
  const parsed = new URL(apiOrigin);
  if (
    !process.env.API_INTERNAL_URL ||
    parsed.protocol !== "https:" ||
    parsed.pathname !== "/" ||
    parsed.search ||
    parsed.hash ||
    parsed.username ||
    parsed.password
  ) {
    throw new Error(
      "Vercel requires API_INTERNAL_URL as an HTTPS backend origin without a path or credentials",
    );
  }
}
const config: NextConfig = {
  distDir: process.env.NEXT_DIST_DIR || ".next",
  output: "standalone",
  devIndicators: false,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin.replace(/\/$/, "")}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "same-origin" },
        ],
      },
    ];
  },
};
export default config;
