import type { Metadata } from "next";
import "./globals.css";
import { LanguageProvider } from "@/components/LanguageProvider";
import { SiteShell } from "@/components/SiteShell";
import { strings } from "@/lib/strings";

export const metadata: Metadata = {
  title: strings.layout.title,
  description: strings.layout.description,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col">
        <LanguageProvider><SiteShell>{children}</SiteShell></LanguageProvider>
      </body>
    </html>
  );
}
