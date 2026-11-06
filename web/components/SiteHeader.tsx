import Link from "next/link";
import { strings } from "@/lib/strings";

const t = strings.layout;

export default function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-hairline bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1080px] flex-wrap items-center justify-between gap-3 px-6 py-3.5">
        <Link href="/" className="text-[19px] font-semibold tracking-tight text-accent hover:no-underline">
          ClearPath
        </Link>
        <nav aria-label={t.navLabel} className="flex flex-wrap gap-7 text-sm">
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
        </nav>
      </div>
    </header>
  );
}
