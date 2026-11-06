"use client";
import { useLanguage } from "@/components/LanguageProvider";
import { LanguageSelector } from "@/components/LanguageSelector";
export function SiteShell({ children }: { children: React.ReactNode }) {
  const { t } = useLanguage();
  return (
    <>
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-indigo-600 focus:text-white focus:rounded-md">{t("skip")}</a>
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 min-h-16 py-2 flex items-center justify-between gap-3">
          <a href="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20 group-hover:bg-indigo-500 transition-colors">CP</div>
            <span className="flex flex-col">
              <span className="font-bold text-lg tracking-tight text-white group-hover:text-indigo-400 transition-colors">ClearPath</span>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold -mt-1">{t("tagline")}</span>
            </span>
          </a>
          <nav aria-label="Main navigation" className="flex items-center gap-3 sm:gap-5 text-sm font-medium">
            <a href="/" className="text-slate-300 hover:text-white focus-visible:ring-2 focus-visible:ring-indigo-400 rounded">{t("newAnalysis")}</a>
            <a href="https://github.com/ClearPath-Team/Clearpath" target="_blank" rel="noreferrer" className="text-slate-400 hover:text-white focus-visible:ring-2 focus-visible:ring-indigo-400 rounded">{t("github")}</a>
            <LanguageSelector />
          </nav>
        </div>
      </header>
      <main id="main-content" className="flex-1">{children}</main>
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500"><div className="max-w-7xl mx-auto px-4">{t("footer")}</div></footer>
    </>
  );
}
