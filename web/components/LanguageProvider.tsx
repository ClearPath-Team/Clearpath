"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { dictionary, type Language, type TranslationKey } from "@/lib/i18n";

const STORAGE_KEY = "clearpath.websiteLanguage";
type LanguageContextValue = {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: TranslationKey) => string;
};
const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored === "en" || stored === "ro") setLanguage(stored);
    } catch {
      // Storage can be unavailable in private browsing.
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    try {
      window.localStorage.setItem(STORAGE_KEY, language);
    } catch {
      // Language switching still works without persistence.
    }
  }, [language]);

  const value = useMemo<LanguageContextValue>(
    () => ({ language, setLanguage, t: (key) => dictionary(language)[key] }),
    [language]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be rendered inside LanguageProvider");
  return context;
}
