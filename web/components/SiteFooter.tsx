import { strings } from "@/lib/strings";

export default function SiteFooter() {
  return (
    <footer className="border-t border-hairline py-6 text-center text-xs text-ink-secondary">
      <div className="mx-auto max-w-[1080px] px-6">{strings.layout.footer}</div>
    </footer>
  );
}
