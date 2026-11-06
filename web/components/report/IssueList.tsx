"use client";

import { useState } from "react";
import { formatSeconds } from "@/lib/format";
import { strings } from "@/lib/strings";
import { SEVERITIES, type Issue, type Severity } from "@/lib/types";
import { SeverityBadge } from "./Severity";

const t = strings.report;
type Category = "visual_contrast" | "screen_reader" | "motor_keyboard" | "structure_navigation";
const CATEGORY_LABELS: Record<Category, { en: string; ro: string }> = {
  visual_contrast: { en: "Contrast", ro: "Contrast" },
  screen_reader: { en: "Screen Reader", ro: "Cititor de ecran" },
  motor_keyboard: { en: "Keyboard", ro: "Tastatură" },
  structure_navigation: { en: "Structure", ro: "Structură" },
};
const CATEGORIES = Object.keys(CATEGORY_LABELS) as Category[];
const KNOWN_RULE_CATEGORIES: Record<string, Category> = {
  "color-contrast": "visual_contrast",
  "link-in-text-block": "visual_contrast",
  "keyboard-trap": "motor_keyboard",
  "nested-interactive": "motor_keyboard",
  "aria-hidden-focus": "motor_keyboard",
  "button-name": "screen_reader",
  "image-alt": "screen_reader",
  "link-name": "screen_reader",
  "label": "screen_reader",
  "select-name": "screen_reader",
  "input-image-alt": "screen_reader",
  "frame-title": "screen_reader",
  "duplicate-id-aria": "screen_reader",
};
function issueCategory(issue: Issue): Category {
  const classified = issue as Issue & { category?: Category };
  if (classified.category && classified.category in CATEGORY_LABELS) return classified.category;
  return KNOWN_RULE_CATEGORIES[issue.rule] ??
    (issue.rule.startsWith("aria-") ? "screen_reader" : "structure_navigation");
}


type Props = {
  issues: Issue[];
  counts: Record<Severity, number>;
  selectedId: string | null;
  lang: string;
  onPlay: (issue: Issue) => void;
};

export default function IssueList({ issues, counts, selectedId, lang, onPlay }: Props) {
  const [filter, setFilter] = useState<"all" | Severity>("all");
  const [category, setCategory] = useState<"all" | Category>("all");
  const visible = issues.filter((issue) =>
    (filter === "all" || issue.severity === filter) &&
    (category === "all" || issueCategory(issue) === category));
  const tabs: { key: "all" | Severity; label: string; count: number }[] = [
    { key: "all", label: t.issues.all, count: issues.length },
    ...SEVERITIES.map((severity) => ({
      key: severity,
      label: t.severity[severity].plural,
      count: counts[severity] ?? issues.filter((issue) => issue.severity === severity).length,
    })),
  ];

  return (
    <section aria-labelledby="issues-title" className="flex min-w-0 flex-[1_1_380px] flex-col gap-4">
      <h2 id="issues-title" className="text-2xl font-bold tracking-[-0.02em]">
        {t.issues.title}
      </h2>
      <div role="group" aria-label={t.issues.filterLabel} className="flex flex-wrap gap-1 rounded bg-[#E8E8ED] p-1">
        {tabs.map((tab) => {
          const on = tab.key === filter;
          return (
            <button
              key={tab.key}
              type="button"
              aria-pressed={on}
              onClick={() => setFilter(tab.key)}
              className={`min-h-9 flex-auto whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-semibold ${
                on ? "bg-white text-accent shadow-hairline" : "text-ink-tertiary hover:text-ink"
              }`}
            >
              {tab.label} <span className="tabular-nums opacity-80">{tab.count}</span>
            </button>
          );
        })}
      </div>

      <div role="group" aria-label={lang === "en" ? "Filter issues by category" : "Filtrează problemele după categorie"} className="flex flex-wrap gap-2">
        {(["all", ...CATEGORIES] as const).map((key) => {
          const selected = category === key;
          const label = key === "all" ? (lang === "en" ? "All categories" : "Toate categoriile")
            : CATEGORY_LABELS[key][lang === "en" ? "en" : "ro"];
          const count = key === "all" ? issues.length
            : issues.filter((issue) => issueCategory(issue) === key).length;
          return (
            <button key={key} type="button" aria-pressed={selected}
              onClick={() => setCategory(key)}
              className={`rounded border px-3 py-2 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${selected ? "border-accent bg-accent text-white" : "border-[#D3D3D9] bg-white text-ink hover:border-accent"}`}>
              {label} <span className="tabular-nums">({count})</span>
            </button>
          );
        })}
      </div>

      {visible.length === 0 ? (
        <p className="rounded bg-surface p-8 text-center text-ink-secondary">{t.issues.empty}</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {visible.map((issue) => {
            const selected = issue.id === selectedId;
            return (
              <li
                key={issue.id}
                className={`flex flex-col gap-2 rounded bg-white px-[22px] py-5 ${
                  selected ? "shadow-[inset_0_0_0_2px_#0076DF]" : "shadow-inset-hairline"
                }`}
              >
                <SeverityBadge severity={issue.severity} />
                <h3 lang={lang} className="text-[17px] font-semibold tracking-[-0.01em]">
                  {issue.title}
                </h3>
                <p lang={lang} className="text-[15px] text-ink-tertiary">
                  {issue.recommendation}
                </p>
                <code className="break-all font-mono text-[13px] text-ink-secondary">{issue.selector}</code>
                <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-2">
                  {issue.timestamp != null ? (
                    <button
                      type="button"
                      onClick={() => onPlay(issue)}
                      className={`inline-flex h-9 items-center gap-2 rounded px-4 text-sm font-semibold ${
                        selected ? "bg-accent text-white" : "bg-white text-accent shadow-inset-hairline hover:bg-surface"
                      }`}
                    >
                      <svg width="10" height="10" viewBox="0 0 16 16" aria-hidden="true">
                        <path d="M4 2.5v11L13 8Z" fill="currentColor" />
                      </svg>
                      {t.playFrom(formatSeconds(issue.timestamp))}
                    </button>
                  ) : (
                    <p className="text-sm text-ink-secondary">{t.issues.notInVideo}</p>
                  )}
                  {issue.help_url && (
                    <a href={issue.help_url} target="_blank" rel="noreferrer" className="text-sm text-link hover:underline">
                      {t.issues.wcagGuide}
                      <span className="sr-only"> {t.issues.opensInNewTab}</span>
                    </a>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
