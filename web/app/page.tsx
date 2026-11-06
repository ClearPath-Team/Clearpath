"use client";

import { useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import type { Language } from "@/lib/i18n";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles, Volume2, ShieldAlert, Video, AlertCircle, Loader2 } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const { language, t } = useLanguage();
  const [manualAnalysisLang, setManualAnalysisLang] = useState<Language | null>(null);
  const selectedAnalysisLang = manualAnalysisLang ?? language;
  const [url, setUrl] = useState("http://localhost:8080/bad-checkout.html");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setError(t("requiredUrl"));
      return;
    }

    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/analyses`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: trimmed, lang: selectedAnalysisLang }),
      });

      if (!res.ok) {
        let msg = t("submitError");
        try {
          const data = await res.json();
          if (data.detail) msg = data.detail;
        } catch {
          // ignore
        }
        setError(msg);
        setLoading(false);
        return;
      }

      const data = await res.json();
      router.push(`/a/${data.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : t("connectionError");
      setError(`${t("connectionError")} (${message})`);
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-16 sm:py-24">
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-800/80 text-indigo-300 text-xs font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          {t("heroBadge")}
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
          {t("heroLead")}{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
            {t("heroAccent")}
          </span>
          {t("heroEnd")}
        </h1>

        <p className="text-lg text-slate-300 leading-relaxed">
          {t("heroDescriptionStart")}{" "}<strong className="text-white font-semibold">{t("heroDescriptionStrong")}</strong>{" "}{t("heroDescriptionEnd")}
        </p>
      </div>

      {/* URL Input Form */}
      <div className="mt-10 max-w-2xl mx-auto">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex flex-col sm:flex-row gap-3 p-2 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={t("urlPlaceholder")}
              disabled={loading}
              aria-label={t("urlLabel")}
              className="flex-1 bg-transparent px-4 py-3 text-white placeholder-slate-500 focus:outline-none text-base disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-60 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {t("starting")}
                </>
              ) : (
                <>
                  {t("analyze")}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          <fieldset className="mt-4 rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <legend className="px-2 text-sm font-semibold text-slate-200">{t("analysisLanguage")}</legend>
            <div className="flex flex-wrap gap-4">
              {(["en", "ro"] as const).map((option) => (
                <label key={option} className="inline-flex cursor-pointer items-center gap-2 text-sm text-slate-200">
                  <input type="radio" name="analysis-language" value={option} checked={selectedAnalysisLang === option}
                    onChange={() => setManualAnalysisLang(option)}
                    className="accent-indigo-500 focus-visible:ring-2 focus-visible:ring-indigo-400" />
                  {option === "en" ? t("english") : t("romanian")}
                </label>
              ))}
            </div>
            <p className="mt-2 text-xs text-slate-400">{t("analysisLanguageHelp")}</p>
          </fieldset>

          {error && (
            <div
              role="alert"
              className="mt-4 p-4 rounded-xl bg-red-950/50 border border-red-800/80 text-red-200 text-sm flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}
        </form>

        <div className="mt-3 text-center">
          <span className="text-xs text-slate-400">
            {t("demoRecommended")}{" "}
            <button
              type="button"
              onClick={() => setUrl("http://localhost:8080/bad-checkout.html")}
              className="text-indigo-400 hover:underline font-mono"
            >
              http://localhost:8080/bad-checkout.html
            </button>
          </span>
        </div>
      </div>

      {/* Feature Highlights */}
      <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-indigo-950 border border-indigo-800 flex items-center justify-center text-indigo-400 mb-4">
            <Volume2 className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">{t("voiceTitle")}</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            {t("voiceDescription")}
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-amber-950 border border-amber-800 flex items-center justify-center text-amber-400 mb-4">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">{t("trapTitle")}</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            {t("trapDescription")}
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-pink-950 border border-pink-800 flex items-center justify-center text-pink-400 mb-4">
            <Video className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">{t("videoTitle")}</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            {t("videoDescription")}
          </p>
        </div>
      </div>
    </div>
  );
}
