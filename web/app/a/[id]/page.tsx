"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { useLanguage } from "@/components/LanguageProvider";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Copy,
  ExternalLink,
  Play,
  RotateCcw,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Volume2,
  Check,
  Loader2,
  Sparkles,
} from "lucide-react";

interface Issue {
  id: string;
  rule?: string;
  rule_id?: string;
  severity?: "critical" | "serious" | "moderate" | "minor";
  impact?: "critical" | "serious" | "moderate" | "minor";
  title?: string;
  description?: string;
  help?: string;
  help_url?: string;
  selector?: string;
  recommendation?: string;
  timestamp?: number | null;
  node_id?: string;
}

interface IssueCounts {
  critical: number;
  serious: number;
  moderate: number;
  minor: number;
  total?: number;
}

interface AnalysisReport {
  id: string;
  url: string;
  title?: string;
  lang?: "en" | "ro";
  score?: number;
  counts?: IssueCounts;
  focus_trap?: boolean;
  duration?: number;
  clip_url?: string;
  issues: Issue[];
}

interface AnalysisStatusResponse {
  id: string;
  lang?: "en" | "ro";
  url: string;
  status: "queued" | "extracting" | "analyzing" | "rendering" | "done" | "failed";
  error: string | null;
  report: AnalysisReport | null;
}


export default function AnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const { t } = useLanguage();
  const STEPS = [
    { key: "queued", label: t("stepQueued"), desc: t("stepQueuedDesc") },
    { key: "extracting", label: t("stepExtracting"), desc: t("stepExtractingDesc") },
    { key: "analyzing", label: t("stepAnalyzing"), desc: t("stepAnalyzingDesc") },
    { key: "rendering", label: t("stepRendering"), desc: t("stepRenderingDesc") },
  ];
  const id = params?.id as string;

  const [data, setData] = useState<AnalysisStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [expandedIssue, setExpandedIssue] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [videoError, setVideoError] = useState(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Polling loop
  useEffect(() => {
    if (!id) return;

    let timer: NodeJS.Timeout;

    const fetchStatus = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/analyses/${id}`);
        if (!res.ok) {
          if (res.status === 404) {
            setError(`${t("analysisNotFound")} ${id}`);
            return;
          }
          throw new Error(`HTTP ${res.status}`);
        }
        const json: AnalysisStatusResponse = await res.json();
        setData(json);

        if (json.status !== "done" && json.status !== "failed") {
          timer = setTimeout(fetchStatus, 1500);
        }
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : t("unknownError");
        setError(`${t("apiConnection")} ${message}`);
      }
    };

    fetchStatus();

    return () => clearTimeout(timer);
  }, [id, apiUrl, t]);

  // Video timeupdate handler
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const seekTo = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play().catch(() => {});
    }
  };

  const handleCopyLink = () => {
    if (typeof window !== "undefined") {
      navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatSeconds = (sec: number | null | undefined) => {
    if (sec === null || sec === undefined) return "—";
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const report = data?.report;

  // Closest issue currently active based on video playback
  const activeIssueId = useMemo(() => {
    if (!report?.issues || currentTime <= 0) return null;
    let closest: Issue | null = null;
    for (const item of report.issues) {
      if (item.timestamp !== null && item.timestamp !== undefined && item.timestamp <= currentTime + 1.5) {
        if (!closest || (item.timestamp > (closest.timestamp ?? 0))) {
          closest = item;
        }
      }
    }
    return closest?.id ?? null;
  }, [report?.issues, currentTime]);

  const filteredIssues = useMemo(() => {
    if (!report?.issues) return [];
    if (filterSeverity === "all") return report.issues;
    return report.issues.filter((i) => (i.severity || i.impact) === filterSeverity);
  }, [report?.issues, filterSeverity]);

  // 1. Loading / Polling in Progress view
  if (data && data.status !== "done" && data.status !== "failed") {
    const activeIndex = STEPS.findIndex((s) => s.key === data.status);
    const currentStepIndex = activeIndex === -1 ? 0 : activeIndex;

    return (
      <div className="max-w-3xl mx-auto px-4 py-20">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-8">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950 text-indigo-300 text-xs font-semibold uppercase tracking-wider border border-indigo-800">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
              {t("inProgress")}
            </div>
            <h1 className="text-2xl font-bold text-white">{t("analyzingExperience")}</h1>
            <p className="text-sm text-slate-400 font-mono break-all">{data.url}</p>
          </div>

          <div className="space-y-4 pt-4">
            {STEPS.map((step, idx) => {
              const isPast = idx < currentStepIndex;
              const isCurrent = idx === currentStepIndex;
              const isFuture = idx > currentStepIndex;

              return (
                <div
                  key={step.key}
                  className={`flex items-start gap-4 p-4 rounded-xl border transition-all ${
                    isCurrent
                      ? "bg-indigo-950/40 border-indigo-700/80 shadow-lg shadow-indigo-950/50"
                      : isPast
                      ? "bg-slate-900/60 border-slate-800 opacity-80"
                      : "bg-slate-950/30 border-slate-900 opacity-40"
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold ${
                      isPast
                        ? "bg-emerald-600 text-white"
                        : isCurrent
                        ? "bg-indigo-600 text-white animate-pulse"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {isPast ? <Check className="w-4 h-4" /> : idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-white">{step.label}</div>
                      {isCurrent && (
                        <span className="text-xs font-medium text-indigo-400 animate-pulse">{t("processing")}</span>
                      )}
                      {isPast && <span className="text-xs text-emerald-400">{t("completed")}</span>}
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">{step.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="text-center text-xs text-slate-500">
            {t("processEstimate")}
          </div>
        </div>
      </div>
    );
  }

  // 2. Failed View
  if (data?.status === "failed" || error) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20">
        <div className="bg-red-950/30 border border-red-800/80 rounded-2xl p-8 text-center space-y-6">
          <div className="w-12 h-12 rounded-2xl bg-red-950 border border-red-800 flex items-center justify-center mx-auto text-red-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-white">{t("failed")}</h1>
            <p className="text-sm text-red-200">
              {error || data?.error || t("unexpectedError")}
            </p>
          </div>
          <button
            onClick={() => router.push("/")}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-semibold text-sm transition-all"
          >
            <RotateCcw className="w-4 h-4" />
            {t("tryAgain")}
          </button>
        </div>
      </div>
    );
  }

  // 3. Completed (Done) Results Dashboard
  if (!report) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mx-auto" />
      </div>
    );
  }

  const score = report.score ?? 0;
  const hasTrap = report.focus_trap ?? false;
  const duration = report.duration ?? 20;
  const rawCounts = report.counts || {
    critical: 0,
    serious: 0,
    moderate: 0,
    minor: 0,
  };
  const totalCount =
    rawCounts.total ??
    (rawCounts.critical + rawCounts.serious + rawCounts.moderate + rawCounts.minor);

  const counts = {
    ...rawCounts,
    total: totalCount || report.issues.length,
  };

  const scoreColor =
    score >= 80
      ? "text-emerald-400 border-emerald-500/40 bg-emerald-950/30"
      : score >= 50
      ? "text-amber-400 border-amber-500/40 bg-amber-950/30"
      : "text-red-400 border-red-500/40 bg-red-950/30";

  const videoUrl = report.clip_url
    ? `${apiUrl}${report.clip_url.startsWith("/") ? "" : "/"}${report.clip_url}`
    : `${apiUrl}/media/${id}/clip.mp4`;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner / Summary Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <span>{t("reportTitle")}</span>
              <span>•</span>
              <span className="font-mono">{report.id}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight break-all">
              {report.url}
            </h1>
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="inline-flex items-center rounded-md border border-indigo-800 bg-indigo-950 px-3 py-1 text-xs font-semibold text-indigo-200">
                {(report.lang || data?.lang || "ro") === "en" ? "🇬🇧 English" : "🇷🇴 Română"}
              </span>
              {hasTrap && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-red-950 border border-red-800 text-red-300 text-xs font-bold">
                  <ShieldAlert className="w-4 h-4 text-red-400" />
                  {t("trapDetected")}
                </span>
              )}
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-md bg-slate-800 text-slate-300 text-xs font-medium">
                <Volume2 className="w-3.5 h-3.5 text-indigo-400" />
                {report.issues.length} {t("identifiedIssues")}
              </span>
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-md bg-slate-800 text-slate-300 text-xs font-medium">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                {t("clipDuration")} {formatSeconds(duration)}
              </span>
            </div>
          </div>

          {/* Score & Actions */}
          <div className="flex items-center gap-6">
            <div className="flex flex-col items-center">
              <div
                className={`w-24 h-24 rounded-2xl border-2 flex flex-col items-center justify-center font-black ${scoreColor}`}
              >
                <span className="text-3xl tracking-tight leading-none">{score}</span>
                <span className="text-[11px] uppercase tracking-wider font-bold opacity-80 mt-1">/ 100</span>
              </div>
              <span className="text-xs text-slate-400 font-semibold mt-1.5">{t("accessibilityScore")}</span>
            </div>

            <div className="flex flex-col gap-2">
              <button
                onClick={handleCopyLink}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all border border-slate-700"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? t("linkCopied") : t("copyLink")}
              </button>
              <button
                onClick={() => router.push("/")}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all"
              >
                <Sparkles className="w-3.5 h-3.5" />
                {t("newAnalysis")}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Video Player on Left, Filterable Violations on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Synchronized Video Player */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl sticky top-24">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
              <div className="flex items-center gap-2 text-sm font-bold text-white">
                <Play className="w-4 h-4 text-indigo-400 fill-indigo-400" />
                {t("narratedDemo")}
              </div>
              <span className="text-xs text-slate-400 font-mono">
                {formatSeconds(currentTime)} / {formatSeconds(videoRef.current?.duration || 20)}
              </span>
            </div>

            <div className="aspect-video bg-black relative flex items-center justify-center">
              <video
                key={videoUrl}
                ref={videoRef}
                controls
                playsInline
                preload="metadata"
                onTimeUpdate={handleTimeUpdate}
                onError={() => setVideoError(true)}
                className="w-full h-full object-contain"
              >
                <source src={videoUrl} type="video/mp4" />
                {t("videoUnsupported")}
              </video>

              {videoError && (
                <div className="absolute inset-0 bg-slate-950/90 flex flex-col items-center justify-center p-6 text-center space-y-3 z-10">
                  <div className="w-10 h-10 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-white">{t("videoFailed")}</p>
                    <p className="text-xs text-slate-400 max-w-sm">
                      {t("videoUnavailable")}
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 text-xs text-slate-400 bg-slate-950/40 border-t border-slate-800/80 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              {t("timestampHelp")}
            </div>
          </div>
        </div>

        {/* Right Column: Interactive Accessibility Violations */}
        <div className="lg:col-span-5 space-y-4">
          {/* Severity Filter Tabs */}
          <div className="flex items-center gap-1.5 p-1.5 bg-slate-900 border border-slate-800 rounded-xl overflow-x-auto text-xs font-semibold">
            {[
              { key: "all", label: t("all"), count: counts.total },
              { key: "critical", label: t("criticalPlural"), count: counts.critical },
              { key: "serious", label: t("seriousPlural"), count: counts.serious },
              { key: "moderate", label: t("moderatePlural"), count: counts.moderate },
              { key: "minor", label: t("minorPlural"), count: counts.minor },
            ].map((f) => (
              <button
                key={f.key}
                onClick={() => setFilterSeverity(f.key)}
                className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap ${
                  filterSeverity === f.key
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                <span>{f.label}</span>
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                    filterSeverity === f.key ? "bg-indigo-900/80 text-indigo-200" : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {f.count}
                </span>
              </button>
            ))}
          </div>

          {/* Issues List */}
          <div className="space-y-3">
            {filteredIssues.length === 0 ? (
              <div className="p-8 rounded-2xl bg-slate-900 border border-slate-800 text-center text-slate-400 text-sm">
                {t("noIssues")}
              </div>
            ) : (
              filteredIssues.map((issue) => {
                const isExpanded = expandedIssue === issue.id;
                const isActive = activeIssueId === issue.id;

                const severity = issue.severity || issue.impact || "minor";
                const ruleName = issue.rule || issue.rule_id || "";
                const title = issue.title || issue.description || ruleName;

                const impactBadge =
                  severity === "critical"
                    ? "bg-red-950 text-red-300 border-red-800"
                    : severity === "serious"
                    ? "bg-amber-950 text-amber-300 border-amber-800"
                    : severity === "moderate"
                    ? "bg-yellow-950 text-yellow-300 border-yellow-800"
                    : "bg-slate-800 text-slate-300 border-slate-700";

                const impactRo =
                  severity === "critical"
                    ? t("critical")
                    : severity === "serious"
                    ? t("serious")
                    : severity === "moderate"
                    ? t("moderate")
                    : t("minor");

                return (
                  <div
                    key={issue.id}
                    className={`rounded-xl border transition-all ${
                      isActive
                        ? "bg-slate-800 border-indigo-500 ring-2 ring-indigo-500/30 shadow-lg"
                        : "bg-slate-900/90 border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="p-4 space-y-2">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${impactBadge}`}
                          >
                            {impactRo}
                          </span>
                          <span className="text-xs font-mono font-bold text-slate-300">{ruleName}</span>
                        </div>

                        {issue.timestamp !== null && issue.timestamp !== undefined ? (
                          <button
                            type="button"
                            onClick={() => seekTo(issue.timestamp!)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-950 hover:bg-indigo-900 border border-indigo-800 text-indigo-300 text-xs font-mono font-bold transition-colors"
                            title={t("seekTitle")}
                          >
                            <Play className="w-3 h-3 fill-indigo-300" />
                            {formatSeconds(issue.timestamp)}
                          </button>
                        ) : (
                          <span className="text-[11px] text-slate-500 font-medium">{t("notInClip")}</span>
                        )}
                      </div>

                      <div
                        className="text-sm text-slate-200 cursor-pointer select-none font-medium leading-snug pt-1"
                        onClick={() => setExpandedIssue(isExpanded ? null : issue.id)}
                      >
                        <div lang={report.lang || "ro"}>{title}</div>
                        {issue.description && (
                          <div lang={report.lang || "ro"} className="text-xs text-slate-400 mt-1 font-normal">
                            {issue.description}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center justify-between pt-1">
                        <button
                          type="button"
                          onClick={() => setExpandedIssue(isExpanded ? null : issue.id)}
                          className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                        >
                          {isExpanded ? (
                            <>
                              {t("hideDetails")} <ChevronUp className="w-3.5 h-3.5" />
                            </>
                          ) : (
                            <>
                              {t("viewRecommendation")} <ChevronDown className="w-3.5 h-3.5" />
                            </>
                          )}
                        </button>

                        {issue.help_url && (
                          <a
                            href={issue.help_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200"
                          >
                            {t("wcagGuide")} <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="px-4 pb-4 pt-2 border-t border-slate-800/80 bg-slate-950/40 rounded-b-xl space-y-3 text-xs">
                        {issue.recommendation && (
                          <div className="space-y-1">
                            <span className="font-semibold text-slate-300 uppercase text-[10px] tracking-wider">
                              {t("recommendation")}
                            </span>
                            <div lang={report.lang || "ro"} className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-900/40 text-indigo-200 leading-relaxed">
                              {issue.recommendation}
                            </div>
                          </div>
                        )}

                        {issue.selector && (
                          <div className="space-y-1">
                            <span className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider">
                              {t("cssSelector")}
                            </span>
                            <pre className="p-2 rounded bg-black/60 font-mono text-[11px] text-slate-300 overflow-x-auto border border-slate-800">
                              <code>{issue.selector}</code>
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
