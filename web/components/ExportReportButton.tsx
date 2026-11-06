"use client";

import { useState } from "react";
import { useLanguage } from "@/components/LanguageProvider";

export default function ExportReportButton({ id, apiUrl }: { id: string; apiUrl: string }) {
  const { language } = useLanguage();
  const ro = language === "ro";
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function download(format: "html" | "json") {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/analyses/${encodeURIComponent(id)}/export?format=${format}`, { signal: AbortSignal.timeout(30000) });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = `clearpath-audit-${id}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch {
      setError(ro ? "Exportul a eșuat. Încearcă din nou." : "Export failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2" aria-label={ro ? "Export raport" : "Export report"} aria-busy={busy}>
        <button type="button" disabled={busy} onClick={() => download("html")} className="rounded bg-accent px-4 py-3 text-white disabled:opacity-50">
          {ro ? "Export HTML / PDF" : "Export HTML / PDF"}
        </button>
        <button type="button" disabled={busy} onClick={() => download("json")} className="rounded border px-4 py-3 disabled:opacity-50">Export JSON</button>
      </div>
      <p className="text-sm text-ink-secondary">{ro ? "Pentru PDF: deschide fișierul HTML și alege Imprimare → Salvare ca PDF." : "For PDF: open the HTML file, then Print → Save as PDF."}</p>
      <p role="status" className="text-sm">{error || (busy ? (ro ? "Se descarcă…" : "Downloading…") : "")}</p>
    </div>
  );
}
