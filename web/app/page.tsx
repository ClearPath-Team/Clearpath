"use client";

import { useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";
import type { Language } from "@/lib/i18n";
import { useRouter } from "next/navigation";
import { AlertCircle, Loader2 } from "lucide-react";
import { useStrings } from "@/lib/useStrings";

const DEMO_URL = "http://localhost:8080/bad-checkout.html";

const PREVIEW_TRANSCRIPT = [
  { time: "0:07", text: "Link", current: false },
  { time: "0:08", text: "Buton", current: true },
  { time: "0:12", text: "Imagine fără descriere", current: false },
  { time: "0:20", text: "Câmp de editare", current: false },
];

const STEP_ICONS = [
  <svg key="tab" width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
    <rect x="3" y="8" width="26" height="16" rx="4" stroke="currentColor" strokeWidth="2" />
    <path d="M9 16h8m-3-3 3 3-3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>,
  <svg key="voice" width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
    <path d="M6 13v6h5l6 5V8l-6 5H6Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    <path d="M21 12a6 6 0 0 1 0 8M24.5 9a10 10 0 0 1 0 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>,
  <svg key="video" width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
    <rect x="4" y="7" width="24" height="18" rx="4" stroke="currentColor" strokeWidth="2" />
    <path d="m14 12 6 4-6 4v-8Z" fill="currentColor" />
  </svg>,
];

export default function HomePage() {
  const strings = useStrings();
  const t = strings.home;
  const { language } = useLanguage();
  const [analysisLanguageOverride, setAnalysisLanguageOverride] = useState<Language | null>(null);
  const analysisLanguage = analysisLanguageOverride ?? language;
  const router = useRouter();
  const [url, setUrl] = useState(DEMO_URL);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setError(t.errors.empty);
      return;
    }

    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/analyses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: trimmed, lang: analysisLanguage }),
      });

      if (!res.ok) {
        let msg: string = t.errors.startFailed;
        try {
          const data = await res.json();
          if (data.detail) msg = data.detail;
        } catch {
          // keep the generic message
        }
        setError(msg);
        setLoading(false);
        return;
      }

      const data = await res.json();
      router.push(`/a/${data.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "";
      setError(message ? `${t.errors.apiUnreachable} (${message})` : t.errors.apiUnreachable);
      setLoading(false);
    }
  };

  return (
    <>
      <section className="mx-auto flex max-w-[880px] flex-col items-center gap-5 px-6 pb-14 pt-24 text-center">
        <p className="text-[19px] font-semibold text-accent">{t.eyebrow}</p>
        <h1 className="text-balance text-[40px] font-bold leading-[1.06] tracking-[-0.035em] sm:text-[64px]">
          {t.title}
        </h1>
        <p className="max-w-[34em] text-balance text-[19px] leading-[1.45] text-ink-secondary sm:text-[21px]">
          {t.lead}
        </p>

        <form onSubmit={handleSubmit} noValidate className="mt-5 flex w-full max-w-[640px] flex-col gap-2.5 text-left">
          <fieldset aria-describedby="analysis-language-help" className="mb-3 rounded border border-hairline p-3">
            <legend className="px-1 text-sm font-medium">{t.analysisLanguage}</legend>
            <div className="flex gap-5">
              {(["en", "ro"] as const).map((lang) => (
                <label key={lang} className="flex items-center gap-2 text-sm">
                  <input type="radio" name="analysis-language" value={lang} checked={analysisLanguage === lang}
                    disabled={loading} onChange={() => setAnalysisLanguageOverride(lang)} className="accent-accent" />
                  {lang === "en" ? t.english : t.romanian}
                </label>
              ))}
            </div>
            <p id="analysis-language-help" className="mt-2 text-xs text-ink-secondary">{t.analysisLanguageHelp}</p>
          </fieldset>
          <label htmlFor="url" className="pl-1 text-sm font-medium text-ink-tertiary">
            {t.urlLabel}
          </label>
          <div className="flex flex-wrap gap-2.5">
            <input
              id="url"
              name="url"
              type="url"
              inputMode="url"
              autoComplete="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={loading}
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? "url-error" : "url-hint"}
              className={`h-14 min-w-0 flex-[1_1_320px] rounded border bg-surface px-5 text-[17px] text-ink disabled:opacity-60 ${
                error ? "border-2 border-critical" : "border-hairline"
              }`}
            />
            <button
              type="submit"
              disabled={loading}
              className="inline-flex h-14 flex-[1_0_auto] items-center justify-center gap-2 rounded bg-accent px-7 sm:flex-none text-[17px] font-semibold text-white hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading && <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />}
              {loading ? t.submitting : t.submit}
            </button>
          </div>
          {error ? (
            <p id="url-error" role="alert" className="flex items-start gap-2 pl-1 text-[15px] text-[#B0000F]">
              <AlertCircle className="mt-0.5 h-[18px] w-[18px] shrink-0" aria-hidden="true" />
              <span>{error}</span>
            </p>
          ) : (
            <p id="url-hint" className="pl-1 text-sm text-ink-secondary">
              {t.hint}{" "}
              <span>
                {t.tryDemo}{" "}
                <button
                  type="button"
                  onClick={() => setUrl(DEMO_URL)}
                  className="break-all text-left font-mono text-[13px] text-link underline-offset-2 hover:underline"
                >
                  {DEMO_URL}
                </button>
              </span>
            </p>
          )}
        </form>
      </section>

      <section aria-label={t.preview.label} className="mx-auto max-w-[1080px] px-6 pb-24 pt-6">
        <div className="flex flex-wrap items-center gap-8 rounded bg-surface p-6 sm:p-10">
          <figure className="m-0 flex min-w-0 flex-[3_1_460px] flex-col gap-3">
            <div
              role="img"
              aria-label={t.preview.frameLabel}
              lang="ro"
              className="relative aspect-video max-w-full overflow-hidden rounded bg-white shadow-hairline [container-type:inline-size]"
            >
              <div className="flex h-[16%] items-center justify-between bg-[#1E293B] px-[5%] text-white" aria-hidden="true">
                <span className="text-[2.4cqw] font-bold">PasUșor</span>
                <span className="flex items-center gap-[2.4cqw] text-[1.8cqw]">
                  <span>Bărbați</span>
                  <span>Femei</span>
                  <span className="inline-block h-[3.6cqw] w-[4.4cqw] rounded-sm border-[3px] border-highlight bg-highlight/10" />
                </span>
              </div>
              <div className="flex flex-col gap-[1.4cqw] px-[18%] py-[5%]" aria-hidden="true">
                <span className="text-[3cqw] font-bold text-[#222]">Finalizează comanda</span>
                <span className="aspect-[16/10] w-[30%] rounded-sm bg-[#E2E8F0]" />
                <span className="h-[1.4cqw] w-[70%] rounded-sm bg-[#E5E7EB]" />
                <span className="h-[1.4cqw] w-[55%] rounded-sm bg-[#EEF0F2]" />
              </div>
              <div
                className="absolute bottom-[6%] left-[10%] right-[10%] rounded-sm bg-black/[0.88] px-[1.4cqw] py-[1cqw] text-center text-[2.6cqw] font-bold text-white"
                aria-hidden="true"
              >
                Buton
              </div>
            </div>
            <figcaption className="text-center text-sm text-ink-secondary">{t.preview.caption}</figcaption>
          </figure>

          <div className="flex min-w-0 flex-[2_1_300px] flex-col gap-3.5">
            <h2 className="text-sm font-semibold text-ink-secondary">{t.preview.transcriptTitle}</h2>
            <ol lang="ro" className="flex flex-col gap-1 text-base">
              {PREVIEW_TRANSCRIPT.map((row) => (
                <li
                  key={row.time}
                  aria-current={row.current ? "true" : undefined}
                  className={`flex gap-3.5 rounded px-3 py-2 ${row.current ? "bg-white font-semibold text-accent" : ""}`}
                >
                  <span className={`w-9 tabular-nums ${row.current ? "" : "text-ink-secondary"}`}>{row.time}</span>
                  <span>„{row.text}”</span>
                </li>
              ))}
            </ol>
            <p className="text-[15px] text-ink-tertiary">
              {t.preview.explanationBefore} <span lang="ro">„Buton”</span> {t.preview.explanationAfter}
            </p>
          </div>
        </div>
      </section>

      <section id="how" aria-labelledby="how-title" className="bg-surface">
        <div className="mx-auto flex max-w-[1080px] flex-col gap-12 px-6 pb-24 pt-20">
          <h2 id="how-title" className="text-center text-[32px] font-bold leading-[1.1] tracking-[-0.03em] sm:text-[44px]">
            {t.steps.title}
          </h2>
          <ol className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-5">
            {t.steps.items.map((step, i) => (
              <li key={step.title} className="flex flex-col gap-3 rounded bg-white p-8">
                <span className="text-accent">{STEP_ICONS[i]}</span>
                <h3 className="text-[21px] font-semibold tracking-[-0.01em]">{step.title}</h3>
                <p className="text-base text-ink-secondary">{step.body}</p>
              </li>
            ))}
          </ol>
          <p className="text-center text-sm text-ink-secondary">{t.steps.limits}</p>
        </div>
      </section>
    </>
  );
}
