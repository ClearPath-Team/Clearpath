"use client";

import Link from "next/link";
import { LanguageSelector } from "@/components/LanguageSelector";
import { useStrings } from "@/lib/useStrings";


export default function SiteHeader() {
  const strings = useStrings();
  const t = strings.layout;
  return (
    <header className="sticky top-0 z-40 border-b border-hairline bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1080px] flex-wrap items-center justify-between gap-3 px-6 py-3.5">
        <Link href="/" className="text-[19px] font-semibold tracking-tight text-accent hover:no-underline">
          ClearPath
        </Link>
        <nav aria-label={t.navLabel} className="flex flex-wrap items-center gap-3 text-sm sm:gap-7">
          <Link href="/#how" className="text-ink-tertiary hover:text-ink">
            {t.howItWorks}
          </Link>
          <Link href="/a/bad-checkout" className="text-ink-tertiary hover:text-ink">
            {t.sampleReport}
          </Link>
          <a
            href="https://github.com/ClearPath-Team/Clearpath"
            target="_blank"
            rel="noreferrer"
            className="text-ink-tertiary hover:text-ink"
          >
            {t.github}
          </a>
          <LanguageSelector />
        </nav>
      </div>
    </header>
  );
}
