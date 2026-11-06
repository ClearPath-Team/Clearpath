import Link from "next/link";
import { strings } from "@/lib/strings";

const t = strings.analysis;

type Props = {
  message: string;
  onRetry: () => void;
  retrying: boolean;
};

export default function AnalysisFailed({ message, onRetry, retrying }: Props) {
  return (
    <div className="mx-auto max-w-[560px] px-6 py-24">
      <div role="alert" className="flex flex-col items-center gap-3 rounded bg-surface px-7 py-8 text-center">
        <svg width="44" height="44" viewBox="0 0 44 44" fill="none" aria-hidden="true" className="text-accent">
          <circle cx="22" cy="22" r="20" stroke="currentColor" strokeWidth="2.5" />
          <path d="M22 12v13" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" />
          <circle cx="22" cy="31" r="1.8" fill="currentColor" />
        </svg>
        <h1 className="text-[22px] font-bold tracking-[-0.02em]">{t.failed.title}</h1>
        <p className="text-[15px] text-ink-tertiary">{t.failed.body}</p>
        <code className="w-full break-words rounded bg-white px-3 py-2.5 text-left font-mono text-[13px] text-ink-secondary">
          {message}
        </code>
        <div className="mt-1 flex flex-wrap justify-center gap-2.5">
          <Link
            href="/"
            className="inline-flex h-11 items-center rounded bg-accent px-5 text-[15px] font-semibold text-white hover:bg-accent-hover"
          >
            {t.newAnalysis}
          </Link>
          <button
            type="button"
            onClick={onRetry}
            disabled={retrying}
            className="inline-flex h-11 items-center rounded bg-white px-5 text-[15px] font-semibold text-accent shadow-inset-hairline hover:bg-white/70 disabled:opacity-70"
          >
            {retrying ? t.failed.retrying : t.failed.tryAgain}
          </button>
        </div>
      </div>
    </div>
  );
}
