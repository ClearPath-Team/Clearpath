import CopyLinkButton from "@/components/CopyLinkButton";
import { strings } from "@/lib/strings";

const t = strings.analysis.progress;

type Props = {
  url: string;
  status: string;
};

function DoneIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="shrink-0">
      <circle cx="12" cy="12" r="11" className="fill-accent" />
      <path d="m7.5 12.5 3 3 6-6.5" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CurrentIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="shrink-0 motion-safe:animate-spin">
      <circle cx="12" cy="12" r="10" stroke="#D2D2D7" strokeWidth="2.5" />
      <path d="M12 2a10 10 0 0 1 10 10" className="stroke-accent" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

function PendingIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="shrink-0">
      <circle cx="12" cy="12" r="10" stroke="#AEAEB2" strokeWidth="2" />
    </svg>
  );
}

export default function AnalysisProgress({ url, status }: Props) {
  const found = t.steps.findIndex((s) => s.key === status);
  const current = found === -1 ? 0 : found;
  const total = t.steps.length;
  const percent = Math.round(((current + 0.5) / total) * 100);

  return (
    <div className="mx-auto flex max-w-[640px] flex-col gap-10 px-6 py-24">
      <div className="flex flex-col items-center gap-3 text-center">
        <h1 className="text-balance text-[36px] font-bold leading-[1.1] tracking-[-0.03em] sm:text-[44px]">{t.title}</h1>
        <p className="break-all text-ink-secondary">{url}</p>
      </div>

      <div
        role="progressbar"
        aria-label={t.barLabel}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={current}
        aria-valuetext={t.stepOf(current + 1, total)}
        className="h-1.5 overflow-hidden rounded-full bg-hairline"
      >
        <div className="h-full rounded-full bg-accent transition-[width] duration-500" style={{ width: `${percent}%` }} />
      </div>

      <p className="sr-only" aria-live="polite">
        {t.liveStatus(t.steps[current].label)}
      </p>

      <ol aria-label={t.stepsLabel} className="rounded bg-surface">
        {t.steps.map((step, i) => {
          const state = i < current ? "done" : i === current ? "current" : "pending";
          return (
            <li
              key={step.key}
              aria-current={state === "current" ? "step" : undefined}
              className={`flex items-center gap-4 border-b border-hairline px-6 py-5 last:border-b-0 ${
                state === "current" ? "rounded bg-white shadow-inset-hairline" : ""
              }`}
            >
              {state === "done" ? <DoneIcon /> : state === "current" ? <CurrentIcon /> : <PendingIcon />}
              <div className="min-w-0 flex-1">
                <p className={`font-semibold ${state === "pending" ? "text-ink-tertiary" : ""}`}>{step.label}</p>
                <p className="text-[15px] text-ink-secondary">{step.desc}</p>
              </div>
              <span
                className={`text-[15px] ${state === "current" ? "font-semibold text-accent" : "text-ink-secondary"}`}
              >
                {state === "done" ? t.done : state === "current" ? t.inProgress : t.upNext}
              </span>
            </li>
          );
        })}
      </ol>

      <div className="flex flex-col items-center gap-4 text-center">
        <p className="text-[15px] text-ink-secondary">{t.note}</p>
        <CopyLinkButton />
      </div>
    </div>
  );
}
