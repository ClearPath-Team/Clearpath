// Shapes from doc/1-foundation/data-contracts.md.
export type Severity = "critical" | "serious" | "moderate" | "minor";

export const SEVERITIES: Severity[] = ["critical", "serious", "moderate", "minor"];

export type IssueCategory = "visual_contrast" | "screen_reader" | "motor_keyboard" | "structure_navigation";
export type WCAGPrinciple = "perceivable" | "operable" | "understandable" | "robust";

export interface Issue {
  id: string;
  rule: string;
  severity: Severity;
  category?: IssueCategory;
  category_label?: { en: string; ro: string };
  wcag_principle?: WCAGPrinciple;
  node_id: string | null;
  selector: string;
  title: string;
  recommendation: string;
  help_url: string | null;
  timestamp: number | null;
}

export interface Report {
  id: string;
  url: string;
  title: string;
  score: number;
  counts: Record<Severity, number>;
  categories?: Record<IssueCategory, number>;
  clip_url: string;
  duration: number;
  focus_trap: boolean;
  issues: Issue[];
  // Analysis language, once the language toggle (M4-03, #36) adds it.
  lang?: string;
}

export interface TimelineEntry {
  seq: number;
  node_id: string | null;
  text: string;
  start: number;
  end: number;
}

export interface Timeline {
  duration: number;
  clip: string;
  entries: TimelineEntry[];
}

export interface AnalysisStatusResponse {
  id: string;
  url: string;
  lang?: "ro" | "en";
  status: "queued" | "extracting" | "analyzing" | "rendering" | "done" | "failed";
  error: string | null;
  report: Report | null;
}
