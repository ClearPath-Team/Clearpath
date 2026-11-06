import type { Metadata } from "next";
import { LanguageProvider } from "@/components/LanguageProvider";
import { SiteShell } from "@/components/SiteShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClearPath — Web Accessibility Simulator",
  description: "Explore accessibility barriers through narrated walkthroughs and WCAG audits.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased">
        <LanguageProvider><SiteShell>{children}</SiteShell></LanguageProvider>
      </body>
    </html>
  );
}
