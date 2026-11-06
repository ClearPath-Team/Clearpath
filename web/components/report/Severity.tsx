"use client";

import { useStrings } from "@/lib/useStrings";
import type { Severity } from "@/lib/types";

// Full class names so Tailwind's scanner keeps them.
export const SEVERITY_STYLE: Record<Severity, { text: string; bg: string; fill: string }> = {
  critical: { text: "text-critical", bg: "bg-critical-bg", fill: "#D70015" },
  serious: { text: "text-serious", bg: "bg-serious-bg", fill: "#B25000" },
  moderate: { text: "text-moderate", bg: "bg-moderate-bg", fill: "#4B49D0" },
  minor: { text: "text-minor", bg: "bg-minor-bg", fill: "#5E5E63" },
};

// Each severity has its own shape so it never relies on color alone.
export function SeverityIcon({ severity, size = 10 }: { severity: Severity; size?: number }) {
  const fill = SEVERITY_STYLE[severity].fill;
  return (
    <svg width={size} height={size} viewBox="0 0 10 10" aria-hidden="true" className="shrink-0">
      {severity === "critical" && <path d="M5 0 10 5 5 10 0 5Z" fill={fill} />}
      {severity === "serious" && <path d="M5 0.5 9.8 9.5H0.2Z" fill={fill} />}
      {severity === "moderate" && <circle cx="5" cy="5" r="5" fill={fill} />}
      {severity === "minor" && <circle cx="5" cy="5" r="4" fill="none" stroke={fill} strokeWidth="2" />}
    </svg>
  );
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const strings = useStrings();
  const style = SEVERITY_STYLE[severity];
  return (
    <span className={`inline-flex items-center gap-1.5 self-start rounded px-2.5 py-0.5 text-[13px] font-semibold ${style.bg} ${style.text}`}>
      <SeverityIcon severity={severity} size={9} />
      {strings.report.severity[severity].label}
    </span>
  );
}
