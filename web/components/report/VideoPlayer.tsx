"use client";

import { useState, type RefObject } from "react";
import VideoErrorPanel from "@/components/analysis/VideoErrorPanel";
import { formatSeconds } from "@/lib/format";
import { useStrings } from "@/lib/useStrings";
import type { Issue } from "@/lib/types";
import { SEVERITY_STYLE } from "./Severity";


type Props = {
  src: string;
  duration: number;
  currentTime: number;
  issues: Issue[];
  videoRef: RefObject<HTMLVideoElement>;
  onTimeUpdate: (seconds: number) => void;
  onPlayIssue: (issue: Issue) => void;
};

export default function VideoPlayer({ src, duration, currentTime, issues, videoRef, onTimeUpdate, onPlayIssue }: Props) {
  const strings = useStrings();
  const t = strings.report;
  const [error, setError] = useState(false);
  const total = duration > 0 ? duration : 1;
  const markers = issues.filter((issue) => issue.timestamp != null);

  return (
    <div className="flex flex-col gap-4">
      <div className="relative aspect-video max-w-full overflow-hidden rounded bg-black shadow-hairline">
        <video
          key={src}
          ref={videoRef}
          controls
          playsInline
          preload="metadata"
          onTimeUpdate={(e) => onTimeUpdate(e.currentTarget.currentTime)}
          onSeeked={(e) => onTimeUpdate(e.currentTarget.currentTime)}
          onError={() => setError(true)}
          className="h-full w-full object-contain"
        >
          <source src={src} type="video/mp4" onError={() => setError(true)} />
          {t.video.unsupported}
        </video>
        {error && <VideoErrorPanel />}
      </div>

      {markers.length > 0 && (
        <div className="px-3">
          <p className="mb-1 text-[13px] font-semibold text-ink-secondary">{t.video.markersLabel}</p>
          <div className="relative h-6">
            <div aria-hidden="true" className="absolute inset-x-0 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-hairline">
              <div
                className="h-full rounded-full bg-accent"
                style={{ width: `${Math.min(100, (currentTime / total) * 100)}%` }}
              />
            </div>
            <ul>
              {markers.map((issue) => {
                const time = formatSeconds(issue.timestamp!);
                return (
                  <li
                    key={issue.id}
                    className="absolute top-0 -translate-x-1/2"
                    style={{ left: `${Math.min(100, (issue.timestamp! / total) * 100)}%` }}
                  >
                    <button
                      type="button"
                      onClick={() => onPlayIssue(issue)}
                      aria-label={t.video.markerLabel(t.severity[issue.severity].label, issue.title, time)}
                      title={`${time} · ${issue.title}`}
                      className="flex h-6 w-6 items-center justify-center rounded-full"
                    >
                      <span
                        className="block h-3.5 w-3.5 rounded-full ring-2 ring-white"
                        style={{ backgroundColor: SEVERITY_STYLE[issue.severity].fill }}
                      />
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
