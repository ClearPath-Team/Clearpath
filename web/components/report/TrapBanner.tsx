"use client";

import { formatSeconds } from "@/lib/format";
import { useStrings } from "@/lib/useStrings";
import type { Issue } from "@/lib/types";


type Props = {
  trapIssue: Issue | undefined;
  onPlay: (issue: Issue) => void;
};

export default function TrapBanner({ trapIssue, onPlay }: Props) {
  const strings = useStrings();
  const t = strings.report;
  const selector = trapIssue?.selector ?? "";
  const time = trapIssue?.timestamp != null ? formatSeconds(trapIssue.timestamp) : null;
  return (
    <section
      aria-labelledby="trap-title"
      className="flex flex-wrap items-center gap-x-6 gap-y-4 rounded bg-accent px-8 py-6 text-white"
    >
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true" className="shrink-0">
        <rect x="5" y="9" width="22" height="14" rx="3" stroke="currentColor" strokeWidth="2" />
        <path d="M11 16h8m-3-3 3 3-3 3M23 12v8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <div className="min-w-0 flex-[1_1_420px]">
        <h2 id="trap-title" className="text-[19px] font-semibold">
          {t.trap.title}
        </h2>
        <p className="text-base">{time ? t.trap.bodyWithTime(time, selector) : t.trap.body(selector)}</p>
      </div>
      {trapIssue && time && (
        <button
          type="button"
          onClick={() => onPlay(trapIssue)}
          className="inline-flex h-11 items-center rounded bg-white px-5 text-[15px] font-semibold text-accent hover:bg-surface focus-visible:outline-white"
        >
          {t.playFrom(time)}
        </button>
      )}
    </section>
  );
}
