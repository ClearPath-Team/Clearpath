"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useLanguage } from "@/components/LanguageProvider";
import { Loader2 } from "lucide-react";
import AnalysisFailed from "@/components/analysis/AnalysisFailed";
import AnalysisProgress from "@/components/analysis/AnalysisProgress";
import CopyLinkButton from "@/components/CopyLinkButton";
import IssueList from "@/components/report/IssueList";
import ReportSummary from "@/components/report/ReportSummary";
import Transcript from "@/components/report/Transcript";
import TrapBanner from "@/components/report/TrapBanner";
import VideoPlayer from "@/components/report/VideoPlayer";
import { formatSeconds } from "@/lib/format";
import { useStrings } from "@/lib/useStrings";
import { SEVERITIES, type AnalysisStatusResponse, type Issue, type Severity, type Timeline } from "@/lib/types";


export default function AnalysisPage() {
  const strings = useStrings();
  const t = strings.report;
  const { language } = useLanguage();
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [data, setData] = useState<AnalysisStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState("");

  const videoRef = useRef<HTMLVideoElement>(null);
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
            setError(strings.analysis.failed.notFound(id));
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
        const message = err instanceof Error ? err.message : String(err);
        setError(strings.analysis.failed.apiUnreachable(message));
      }
    };

    fetchStatus();

    return () => clearTimeout(timer);
  }, [id, apiUrl, strings]);

  // The transcript is fetched once the analysis is done (M4-09 endpoint).
  const isDone = data?.status === "done";
  useEffect(() => {
    if (!isDone || !id) return;
    let cancelled = false;
    fetch(`${apiUrl}/api/analyses/${id}/timeline`)
      .then((res) => (res.ok ? res.json() : null))
      .then((json: Timeline | null) => {
        if (!cancelled) setTimeline(json);
      })
      .catch(() => {
        if (!cancelled) setTimeline(null);
      });
    return () => {
      cancelled = true;
    };
  }, [isDone, id, apiUrl]);

  const report = data?.report ?? null;

  const issueSeverityByNode = useMemo(() => {
    const map = new Map<string, Severity>();
    for (const issue of report?.issues ?? []) {
      if (!issue.node_id) continue;
      const existing = map.get(issue.node_id);
      if (!existing || SEVERITIES.indexOf(issue.severity) < SEVERITIES.indexOf(existing)) {
        map.set(issue.node_id, issue.severity);
      }
    }
    return map;
  }, [report]);

  const seekTo = (seconds: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = seconds;
    setCurrentTime(seconds);
    video.play().catch(() => {});
    video.scrollIntoView({ block: "nearest" });
  };

  const playIssue = (issue: Issue) => {
    if (issue.timestamp == null) return;
    setSelectedIssueId(issue.id);
    setAnnouncement(t.video.nowPlaying(formatSeconds(issue.timestamp), issue.title));
    seekTo(issue.timestamp);
  };

  // Re-runs the same URL for a failed analysis; without one (unknown id, API down) it reloads this page.
  const retry = async () => {
    if (!data?.url) {
      window.location.reload();
      return;
    }
    setRetrying(true);
    try {
      const res = await fetch(`${apiUrl}/api/analyses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: data.url, lang: data.lang ?? data.report?.lang ?? language }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      router.push(`/a/${json.id}`);
    } catch {
      setRetrying(false);
      window.location.reload();
    }
  };

  if (data && data.status !== "done" && data.status !== "failed") {
    return <AnalysisProgress url={data.url} status={data.status} />;
  }

  if (data?.status === "failed" || error) {
    return (
      <AnalysisFailed
        message={error || data?.error || strings.analysis.failed.unknownError}
        onRetry={retry}
        retrying={retrying}
      />
    );
  }

  if (!report) {
    return (
      <div className="mx-auto flex max-w-2xl items-center justify-center gap-3 px-6 py-24 text-ink-secondary" role="status">
        <Loader2 className="h-5 w-5 motion-safe:animate-spin" aria-hidden="true" />
        {strings.analysis.loading}
      </div>
    );
  }

  // Backend content (titles, recommendations, announcements) is in the analysis language.
  const contentLang = report.lang ?? data?.lang ?? "ro";
  const videoUrl = report.clip_url
    ? `${apiUrl}${report.clip_url.startsWith("/") ? "" : "/"}${report.clip_url}`
    : `${apiUrl}/media/${id}/clip.mp4`;
  const trapIssue = report.issues.find((issue) => issue.rule === "keyboard-trap");

  return (
    <div className="mx-auto flex max-w-[1240px] flex-col gap-10 px-6 pb-24 pt-14">
      <p className="sr-only" aria-live="polite">
        {announcement}
      </p>

      <div className="flex flex-wrap items-end justify-between gap-5">
        <div className="flex min-w-0 flex-[1_1_480px] flex-col gap-1.5">
          <p className="text-[15px] font-semibold text-ink-secondary">{t.eyebrow}</p>
          <h1 lang={contentLang} className="text-[36px] font-bold leading-[1.08] tracking-[-0.035em] sm:text-[48px]">
            {report.title || report.url}
          </h1>
          <p className="break-all text-base text-ink-secondary">{report.url}</p>
        </div>
        <CopyLinkButton />
      </div>

      <ReportSummary score={report.score} counts={report.counts} />

      {report.focus_trap && <TrapBanner trapIssue={trapIssue} onPlay={playIssue} />}

      <div className="flex flex-wrap items-start gap-8">
        <section aria-labelledby="clip-title" className="flex min-w-0 flex-[999_1_560px] flex-col gap-4">
          <h2 id="clip-title" className="text-2xl font-bold tracking-[-0.02em]">
            {t.video.title}
          </h2>
          <VideoPlayer
            src={videoUrl}
            duration={report.duration}
            currentTime={currentTime}
            issues={report.issues}
            videoRef={videoRef}
            onTimeUpdate={setCurrentTime}
            onPlayIssue={playIssue}
          />
          <Transcript
            entries={timeline?.entries ?? null}
            currentTime={currentTime}
            issueSeverityByNode={issueSeverityByNode}
            lang={contentLang}
            onSeek={seekTo}
          />
        </section>

        <IssueList
          issues={report.issues}
          counts={report.counts}
          selectedId={selectedIssueId}
          lang={contentLang}
          onPlay={playIssue}
        />
      </div>
    </div>
  );
}
