"use client";

import { useState } from "react";
import { strings } from "@/lib/strings";

const t = strings.analysis;

export default function CopyLinkButton() {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setState("copied");
    } catch {
      // Clipboard is unavailable on non-secure origins or when permission is denied.
      setState("failed");
    }
    setTimeout(() => setState("idle"), 2500);
  };

  return (
    <button
      type="button"
      onClick={copy}
      className="inline-flex h-11 items-center rounded bg-white px-5 text-[15px] font-semibold text-accent shadow-inset-hairline hover:bg-surface"
    >
      <span aria-live="polite">
        {state === "copied" ? t.linkCopied : state === "failed" ? t.copyFailed : t.copyLink}
      </span>
    </button>
  );
}
