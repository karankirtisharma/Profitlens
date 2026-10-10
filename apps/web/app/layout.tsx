import type { Metadata, Viewport } from "next";
import "./globals.css";
import { ExperienceProvider } from "../components/experience";
export const metadata: Metadata = {
  title: "ProfitLens | Business workspace",
  description:
    "Organize business records, validate imports, and review contract evidence.",
};
export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#e7ebef" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0c0f" },
  ],
};
// Applies a saved theme choice before first paint; the system preference is the default.
const themeScript = `try{var t=localStorage.getItem("profitlens.theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}`;
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <ExperienceProvider>{children}</ExperienceProvider>
      </body>
    </html>
  );
}
