"use client";

import { useStrings } from "@/lib/useStrings";


export default function VideoErrorPanel() {
  const strings = useStrings();
  const t = strings.analysis.video;
  return (
    <div
      role="status"
      className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2.5 bg-ink p-6 text-center text-white"
    >
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none" aria-hidden="true">
        <rect x="4" y="8" width="28" height="20" rx="4" stroke="currentColor" strokeWidth="2" />
        <path d="m6 6 24 24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <p className="text-[17px] font-semibold">{t.errorTitle}</p>
      <p className="text-sm text-[#D9E0EA]">{t.errorBody}</p>
    </div>
  );
}
