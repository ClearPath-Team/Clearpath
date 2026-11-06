import { strings } from "@/lib/strings";
import { SEVERITIES, type Severity } from "@/lib/types";
import { SEVERITY_STYLE, SeverityIcon } from "./Severity";

const t = strings.report;

type Props = {
  score: number;
  counts: Record<Severity, number>;
};

export default function ReportSummary({ score, counts }: Props) {
  const clamped = Math.max(0, Math.min(100, score));
  return (
    <section aria-label={t.summaryLabel} className="flex flex-wrap gap-5">
      <div className="flex min-w-0 flex-[1_1_260px] flex-col gap-1 rounded bg-surface px-8 py-7">
        <p className="text-[15px] font-semibold text-ink-secondary">{t.score}</p>
        <p className="flex items-baseline gap-1.5">
          <span className="text-[72px] font-bold leading-none tracking-[-0.05em] text-accent tabular-nums sm:text-[88px]">
            {score}
          </span>
          <span className="text-2xl font-semibold text-ink-secondary">{t.outOf}</span>
        </p>
        <div aria-hidden="true" className="mt-3.5 h-1.5 overflow-hidden rounded-full bg-hairline">
          <div className="h-full rounded-full bg-accent" style={{ width: `${clamped}%` }} />
        </div>
      </div>
      <dl className="grid min-w-0 flex-[2_1_420px] grid-cols-[repeat(auto-fit,minmax(110px,1fr))] content-center gap-4 rounded bg-surface px-8 py-7">
        {SEVERITIES.map((severity) => (
          <div key={severity} className="flex flex-col-reverse gap-1">
            <dt className={`flex items-center gap-1.5 text-[15px] font-semibold ${SEVERITY_STYLE[severity].text}`}>
              <SeverityIcon severity={severity} />
              {t.severity[severity].plural}
            </dt>
            <dd className="text-[40px] font-bold leading-[1.1] tracking-[-0.03em] tabular-nums">{counts[severity] ?? 0}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
