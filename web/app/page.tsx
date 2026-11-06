"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles, Volume2, ShieldAlert, Video, AlertCircle, Loader2 } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [url, setUrl] = useState("http://localhost:8080/bad-checkout.html");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setError("Te rugăm să introduci o adresă URL validă.");
      return;
    }

    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/analyses`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: trimmed }),
      });

      if (!res.ok) {
        let msg = "A apărut o eroare la inițierea analizei.";
        try {
          const data = await res.json();
          if (data.detail) msg = data.detail;
        } catch {
          // ignore
        }
        setError(msg);
        setLoading(false);
        return;
      }

      const data = await res.json();
      router.push(`/a/${data.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Nu s-a putut conecta la serverul API";
      setError(`Nu s-a putut conecta la serverul API (FastAPI :8000). Asigură-te că rulează api/main.py. (${message})`);
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-16 sm:py-24">
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-800/80 text-indigo-300 text-xs font-semibold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          Simulare & Audit de Accesibilitate Web
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
          Fă experiența utilizatorilor nevăzători{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
            vizibilă și auzită
          </span>
          .
        </h1>

        <p className="text-lg text-slate-300 leading-relaxed">
          Pornind de la o simplă adresă web, ClearPath simulează un screen reader în limba română (NVDA),
          detectează capcanele de tastatură, rulează un audit WCAG și generează un{" "}
          <strong className="text-white font-semibold">clip video narat și sincronizat</strong> pentru a demonstra
          impactul real al barierelor de accesibilitate.
        </p>
      </div>

      {/* URL Input Form */}
      <div className="mt-10 max-w-2xl mx-auto">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex flex-col sm:flex-row gap-3 p-2 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://exemplu.ro sau http://localhost:8080/..."
              disabled={loading}
              aria-label="Adresa web de analizat"
              className="flex-1 bg-transparent px-4 py-3 text-white placeholder-slate-500 focus:outline-none text-base disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-60 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Se inițiază...
                </>
              ) : (
                <>
                  Analizează pagina
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {error && (
            <div
              role="alert"
              className="mt-4 p-4 rounded-xl bg-red-950/50 border border-red-800/80 text-red-200 text-sm flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}
        </form>

        <div className="mt-3 text-center">
          <span className="text-xs text-slate-400">
            Pagina demo recomandată:{" "}
            <button
              type="button"
              onClick={() => setUrl("http://localhost:8080/bad-checkout.html")}
              className="text-indigo-400 hover:underline font-mono"
            >
              http://localhost:8080/bad-checkout.html
            </button>
          </span>
        </div>
      </div>

      {/* Feature Highlights */}
      <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-indigo-950 border border-indigo-800 flex items-center justify-center text-indigo-400 mb-4">
            <Volume2 className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">Simulare Vocală NVDA</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            Sintetizează anunțurile narate în limba română (vocea Mihai, Piper TTS) exact așa cum le percepe un
            utilizator cu dizabilități vizuale navigând secvențial cu tasta Tab.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-amber-950 border border-amber-800 flex items-center justify-center text-amber-400 mb-4">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">Detecție Capcane Tastatură</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            Identifică automat buclele de focalizare în care utilizatorul rămâne blocat, semnalând problema critică
            și scăzând corespunzător scorul de accesibilitate.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-pink-950 border border-pink-800 flex items-center justify-center text-pink-400 mb-4">
            <Video className="w-5 h-5" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">Video Sincronizat</h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            Fiecare problemă descoperită este marcată cu timestamp exact în clipul video. Un simplu click pe
            orice eroare derulează automat videoul la momentul incidentului.
          </p>
        </div>
      </div>
    </div>
  );
}
