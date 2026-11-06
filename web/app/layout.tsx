import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClearPath — Accesibilitate Web Vizibilă și Auzită",
  description:
    "Transformă navigarea asistivă a utilizatorilor nevăzători într-o demonstrație video narată și sincronizată cu un audit complet de accesibilitate WCAG.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ro">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-indigo-600 focus:text-white focus:rounded-md"
        >
          Sari la conținutul principal
        </a>
        <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <a href="/" className="flex items-center gap-2 group">
                <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20 group-hover:bg-indigo-500 transition-colors">
                  CP
                </div>
                <div className="flex flex-col">
                  <span className="font-bold text-lg tracking-tight text-white group-hover:text-indigo-400 transition-colors">
                    ClearPath
                  </span>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold -mt-1">
                    Accessibility Simulator
                  </span>
                </div>
              </a>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-950 text-indigo-300 border border-indigo-800">
                Astra Hack 2026
              </span>
            </div>

            <nav className="flex items-center gap-4 text-sm font-medium">
              <a
                href="/"
                className="text-slate-300 hover:text-white transition-colors"
              >
                Analiză nouă
              </a>
              <a
                href="https://github.com/ClearPath-Team/Clearpath"
                target="_blank"
                rel="noreferrer"
                className="text-slate-400 hover:text-white transition-colors"
              >
                GitHub
              </a>
            </nav>
          </div>
        </header>

        <main id="main-content" className="flex-1">
          {children}
        </main>

        <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4">
            ClearPath • Proiect dezvoltat de echipa Four The Win pentru Astra Hack • Noiembrie 2026
          </div>
        </footer>
      </body>
    </html>
  );
}
