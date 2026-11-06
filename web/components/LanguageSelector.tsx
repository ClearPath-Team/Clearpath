"use client";

import { useLanguage } from "@/components/LanguageProvider";

export function LanguageSelector() {
  const { language, setLanguage, t } = useLanguage();
  return (
    <div className="flex items-center gap-2">
      <label htmlFor="website-language" className="sr-only">{t("language")}</label>
      <select
        id="website-language"
        aria-label={t("language")}
        value={language}
        onChange={(event) => setLanguage(event.target.value as "en" | "ro")}
        className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
      >
        <option value="en">English</option>
        <option value="ro">Română</option>
      </select>
    </div>
  );
}
