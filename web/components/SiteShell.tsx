"use client";

import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import { useStrings } from "@/lib/useStrings";

export function SiteShell({ children }: { children: React.ReactNode }) {
  const strings = useStrings();
  return (
    <>
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-accent focus:px-4 focus:py-2 focus:text-white">
        {strings.layout.skipToContent}
      </a>
      <SiteHeader />
      <main id="main-content" className="flex-1">{children}</main>
      <SiteFooter />
    </>
  );
}
