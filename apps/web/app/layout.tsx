import type { Metadata } from "next";
import "./globals.css";
import { ExperienceProvider } from "../components/experience";
export const metadata: Metadata = {
  title: "ProfitLens | Business workspace",
  description:
    "Organize business records, validate imports, and review contract evidence.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <ExperienceProvider>{children}</ExperienceProvider>
      </body>
    </html>
  );
}
