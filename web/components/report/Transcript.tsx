"use client";

import { useEffect, useRef } from "react";
import { formatSeconds } from "@/lib/format";
import { useStrings } from "@/lib/useStrings";
import type { Severity, TimelineEntry } from "@/lib/types";
import { SEVERITY_STYLE } from "./Severity";


type Props = {
  entries: TimelineEntry[] | null;
  currentTime: number;
  // node_id -> most severe issue on that node
  issueSeverityByNode: Map<string, Severity>;
  lang: string;
  onSeek: (seconds: number) => void;
};

export default function Transcript({ entries, currentTime, issueSeverityByNode, lang, onSeek }: Props) {
  const strings = useStrings();
  const t = strings.report.transcript;
  const listRef = useRef<HTMLOListElement>(null);
  const rowRefs = useRef<(HTMLLIElement | null)[]>([]);

  let currentIndex = -1;
  if (entries && currentTime > 0) {
    entries.forEach((entry, i) => {
      if (entry.start <= currentTime + 0.05) currentIndex = i;
    });
  }

  // Keep the playing row visible by scrolling the list itself, never the page.
  useEffect(() => {
    const list = listRef.current;
    const row = rowRefs.current[currentIndex];
    if (!list || !row) return;
    const above = row.offsetTop < list.scrollTop;
    const below = row.offsetTop + row.offsetHeight > list.scrollTop + list.clientHeight;
    if (above || below) {
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      list.scrollTo({ top: row.offsetTop - list.clientHeight / 3, behavior: reduce ? "auto" : "smooth" });
    }
  }, [currentIndex]);

  return (
    <section aria-labelledby="transcript-title" className="rounded bg-surface p-5">
      <h3 id="transcript-title" className="mb-2.5 ml-2 text-[15px] font-semibold text-ink-secondary">
        {t.title}
      </h3>
      {!entries ? (
        <p className="ml-2 text-[15px] text-ink-secondary">{t.unavailable}</p>
      ) : (
        <ol ref={listRef} lang={lang} className="relative flex max-h-[340px] flex-col gap-0.5 overflow-y-auto">
          {entries.map((entry, i) => {
            const current = i === currentIndex;
            const severity = entry.node_id ? issueSeverityByNode.get(entry.node_id) : undefined;
            const time = formatSeconds(entry.start);
            return (
              <li
                key={entry.seq}
                ref={(el) => {
                  rowRefs.current[i] = el;
                }}
                aria-current={current ? "true" : undefined}
              >
                <button
                  type="button"
                  onClick={() => onSeek(entry.start)}
                  aria-label={t.seekLabel(time, entry.text)}
                  className={`flex w-full items-center gap-3.5 rounded px-2.5 py-2 text-left ${
                    current ? "bg-white font-semibold text-accent" : "hover:bg-white/60"
                  }`}
                >
                  <span className={`w-10 shrink-0 text-[15px] tabular-nums ${current ? "" : "text-ink-secondary"}`}>
                    {time}
                  </span>
                  <span className="min-w-0 flex-1">„{entry.text}”</span>
                  {severity && (
                    <span
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ backgroundColor: SEVERITY_STYLE[severity].fill }}
                      title={t.hasIssue}
                    />
                  )}
                </button>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
