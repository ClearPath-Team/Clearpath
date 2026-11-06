"use client";

import { useLanguage } from "@/components/LanguageProvider";
import { romanianStrings, strings } from "@/lib/strings";

export function useStrings() {
  const { language } = useLanguage();
  return language === "ro" ? romanianStrings : strings;
}
