// Interface copy; backend-generated announcements and findings keep their own language.
export const strings = {
  layout: {
    title: "ClearPath — Hear your site the way a blind user does",
    description:
      "ClearPath navigates a web page with the keyboard only, reads it aloud like a screen reader, and returns a narrated video synchronized with a WCAG accessibility report.",
    skipToContent: "Skip to main content",
    navLabel: "Main",
    howItWorks: "How it works",
    sampleReport: "Sample report",
    github: "GitHub",
    footer: "ClearPath · Built by team Four The Win for Astra Hack · November 2026",
  },
  home: {
    eyebrow: "Accessibility, heard.",
    title: "Hear your site the way a blind user does.",
    lead: "ClearPath navigates your page with the keyboard only, reads it aloud in your chosen language, and shows every issue in a narrated video.",
    urlLabel: "Web address to analyze",
    submit: "Analyze",
    submitting: "Starting…",
    hint: "Usually under 3 minutes. One page, no sign-in.",
    tryDemo: "Try the demo page:",
    analysisLanguage: "Analysis narration language",
    analysisLanguageHelp: "Choose the narration language independently of the website language.",
    english: "English",
    romanian: "Romanian",
    errors: {
      empty: "Please enter a web address.",
      startFailed: "The analysis couldn’t be started.",
      apiUnreachable:
        "Can’t reach the ClearPath API (FastAPI on port 8000). Make sure api/main.py is running.",
    },
    preview: {
      label: "Report preview",
      frameLabel:
        "Video frame: the cart button is outlined in yellow while the screen reader says “Buton”.",
      caption: "The narrated video highlights the element the screen reader is announcing.",
      transcriptTitle: "What the user hears",
      explanationBefore: "The cart button has no name. A blind user only hears",
      explanationAfter: "(button) and can’t tell what it does.",
    },
    steps: {
      title: "Three steps. One link.",
      items: [
        {
          title: "We tab through the page",
          body: "We read the accessibility tree and focus order exactly as someone without a mouse would. Keyboard traps surface here.",
        },
        {
          title: "We read it aloud",
          body: "Every element is announced following NVDA conventions, and an axe-core audit checks the WCAG rules.",
        },
        {
          title: "You get the video and the report",
          body: "A narrated video, a 0–100 score, and every issue linked to its exact second in the clip.",
        },
      ],
      limits: "One page per analysis, no sign-in, up to 40 announcements (about 90 seconds).",
    },
  },
  analysis: {
    newAnalysis: "New analysis",
    copyLink: "Copy link",
    linkCopied: "Link copied",
    copyFailed: "Copy the address from the browser bar",
    loading: "Loading analysis…",
    progress: {
      title: "Listening to your page.",
      barLabel: "Analysis progress",
      stepOf: (step: number, total: number) => `Step ${step} of ${total}`,
      stepsLabel: "Analysis steps",
      done: "Done",
      inProgress: "In progress",
      upNext: "Up next",
      liveStatus: (label: string) => `In progress: ${label}`,
      note: "Usually under 3 minutes. You can close this page; the link stays valid.",
      steps: [
        { key: "queued", label: "Preparing the session", desc: "Chromium browser, 1280 × 720 viewport." },
        { key: "extracting", label: "Accessibility tree", desc: "Page structure and Tab order." },
        { key: "analyzing", label: "Screen reader and WCAG audit", desc: "Announcements and axe-core rules." },
        { key: "rendering", label: "Narrated video", desc: "Recording, highlighting, and voice sync." },
      ],
    },
    failed: {
      title: "The analysis couldn’t be completed",
      body: "Check the address or try again in a few minutes.",
      unknownError: "The pipeline stopped unexpectedly.",
      notFound: (id: string) => `No analysis found with id “${id}”.`,
      apiUnreachable: (message: string) => `Can’t reach the ClearPath API: ${message}`,
      tryAgain: "Try again",
      retrying: "Starting…",
    },
    video: {
      errorTitle: "The video couldn’t be played",
      errorBody: "The report and the issues found are still available.",
    },
  },
  report: {
    eyebrow: "Accessibility report",
    summaryLabel: "Summary",
    score: "Accessibility score",
    outOf: "/ 100",
    severity: {
      critical: { label: "Critical", plural: "Critical" },
      serious: { label: "Serious", plural: "Serious" },
      moderate: { label: "Moderate", plural: "Moderate" },
      minor: { label: "Minor", plural: "Minor" },
    },
    trap: {
      title: "Keyboard trap",
      bodyWithTime: (time: string, selector: string) =>
        `At ${time}, keyboard focus gets stuck on ${selector}. Someone using only the keyboard can’t move past it.`,
      body: (selector: string) =>
        `Keyboard focus gets stuck on ${selector}. Someone using only the keyboard can’t move past it.`,
    },
    playFrom: (time: string) => `Play from ${time}`,
    video: {
      title: "Narrated video",
      unsupported: "Your browser can’t play this video.",
      markersLabel: "Issues in the video",
      markerLabel: (severity: string, title: string, time: string) => `${severity} issue at ${time}: ${title}`,
      nowPlaying: (time: string, title: string) => `Playing from ${time}: ${title}`,
    },
    transcript: {
      title: "What the user hears",
      unavailable: "The transcript isn’t available for this analysis.",
      seekLabel: (time: string, text: string) => `Play from ${time}: ${text}`,
      hasIssue: "has an issue",
    },
    issues: {
      title: "Issues found",
      filterLabel: "Filter by severity",
      all: "All",
      empty: "No issues at this severity.",
      notInVideo: "Not in the video: this issue affects the whole page.",
      wcagGuide: "WCAG guidance",
      opensInNewTab: "(opens in a new tab)",
    },
  },
} as const;

type Localized<T> = T extends string ? string
  : T extends (...args: never[]) => unknown ? T
  : T extends readonly (infer Item)[] ? readonly Localized<Item>[]
  : { [K in keyof T]: Localized<T[K]> };

export const romanianStrings: Localized<typeof strings> = {
  layout: {
    ...strings.layout,
    title: "ClearPath — Ascultă-ți site-ul altfel",
    description: "Navigare asistată, audit WCAG și video narat, într-un singur raport.",
    skipToContent: "Sari la conținutul principal", navLabel: "Navigare principală",
    howItWorks: "Cum funcționează", sampleReport: "Raport exemplu",
    footer: "ClearPath · Creat de echipa Four The Win pentru Astra Hack · Noiembrie 2026",
  },
  home: {
    eyebrow: "Accesibilitatea se aude.", title: "Ascultă-ți site-ul așa cum îl aude un utilizator nevăzător.",
    lead: "ClearPath navighează pagina folosind doar tastatura, o citește în limba aleasă și arată fiecare problemă într-un clip narat.",
    urlLabel: "Adresa web de analizat", submit: "Analizează", submitting: "Se inițiază…",
    hint: "De obicei sub 3 minute. O pagină, fără autentificare.", tryDemo: "Încearcă pagina demo:",
    analysisLanguage: "Limba narării analizei", analysisLanguageHelp: "Poți alege limba narării independent de limba interfeței.",
    english: "Engleză", romanian: "Română",
    errors: { empty: "Introdu o adresă web.", startFailed: "Analiza nu a putut fi inițiată.",
      apiUnreachable: "Nu se poate conecta la API-ul ClearPath (FastAPI pe portul 8000). Verifică dacă api/main.py rulează." },
    preview: { label: "Previzualizare raport", frameLabel: "Cadru video: coșul este evidențiat cu galben, iar cititorul de ecran spune „Buton”.",
      caption: "Clipul narat evidențiază elementul anunțat de cititorul de ecran.", transcriptTitle: "Ce aude utilizatorul",
      explanationBefore: "Butonul coșului nu are nume. Un utilizator nevăzător aude doar", explanationAfter: "și nu știe ce face." },
    steps: { title: "Trei pași. Un singur link.", items: [
      { title: "Navigăm cu Tab", body: "Citim arborele de accesibilitate și ordinea focalizării așa cum le întâlnește cineva fără mouse. Detectăm capcanele de tastatură." },
      { title: "Citim pagina cu voce tare", body: "Anunțăm fiecare element după convențiile NVDA și verificăm regulile WCAG folosind axe-core." },
      { title: "Primești clipul și raportul", body: "Un clip narat, un scor de la 0 la 100 și fiecare problemă legată de secunda ei din înregistrare." },
    ], limits: "O pagină per analiză, fără autentificare, până la 40 de anunțuri (aproximativ 90 de secunde)." },
  },
  analysis: {
    newAnalysis: "Analiză nouă", copyLink: "Copiază linkul", linkCopied: "Link copiat", copyFailed: "Copiază adresa din bara browserului", loading: "Se încarcă analiza…",
    progress: { title: "Ascultăm pagina ta.", barLabel: "Progresul analizei", stepOf: (step, total) => `Pasul ${step} din ${total}`,
      stepsLabel: "Pașii analizei", done: "Finalizat", inProgress: "În desfășurare", upNext: "Urmează",
      liveStatus: (label) => `În desfășurare: ${label}`, note: "De obicei sub 3 minute. Poți închide pagina; linkul rămâne valid.",
      steps: [ { key: "queued", label: "Pregătirea sesiunii", desc: "Browser Chromium, rezoluție 1280 × 720." },
        { key: "extracting", label: "Arborele de accesibilitate", desc: "Structura paginii și ordinea Tab." },
        { key: "analyzing", label: "Cititor de ecran și audit WCAG", desc: "Anunțuri și reguli axe-core." },
        { key: "rendering", label: "Clipul narat", desc: "Înregistrare, evidențiere și sincronizare vocală." } ] },
    failed: { title: "Analiza nu a putut fi finalizată", body: "Verifică adresa sau încearcă din nou peste câteva minute.",
      unknownError: "Procesarea s-a oprit neașteptat.", notFound: (id) => `Nu există o analiză cu identificatorul „${id}”.`,
      apiUnreachable: (message) => `Nu se poate conecta la API-ul ClearPath: ${message}`, tryAgain: "Încearcă din nou", retrying: "Se inițiază…" },
    video: { errorTitle: "Clipul video nu a putut fi redat", errorBody: "Raportul și problemele găsite sunt în continuare disponibile." },
  },
  report: {
    eyebrow: "Raport de accesibilitate", summaryLabel: "Rezumat", score: "Scor de accesibilitate", outOf: "/ 100",
    severity: { critical: { label: "Critic", plural: "Critice" }, serious: { label: "Grav", plural: "Grave" },
      moderate: { label: "Mediu", plural: "Medii" }, minor: { label: "Minor", plural: "Minore" } },
    trap: { title: "Capcană de tastatură", bodyWithTime: (time, selector) => `La ${time}, focalizarea se blochează pe ${selector}. Cineva care folosește doar tastatura nu poate continua.`,
      body: (selector) => `Focalizarea se blochează pe ${selector}. Cineva care folosește doar tastatura nu poate continua.` },
    playFrom: (time) => `Redă de la ${time}`,
    video: { title: "Clip narat", unsupported: "Browserul tău nu poate reda acest clip.", markersLabel: "Probleme în clip",
      markerLabel: (severity, title, time) => `Problemă de severitate ${severity} la ${time}: ${title}`,
      nowPlaying: (time, title) => `Redare de la ${time}: ${title}` },
    transcript: { title: "Ce aude utilizatorul", unavailable: "Transcriptul nu este disponibil pentru această analiză.",
      seekLabel: (time, text) => `Redă de la ${time}: ${text}`, hasIssue: "are o problemă" },
    issues: { title: "Probleme găsite", filterLabel: "Filtrează după severitate", all: "Toate", empty: "Nu există probleme de această severitate.",
      notInVideo: "Nu apare în clip: această problemă afectează întreaga pagină.", wcagGuide: "Ghid WCAG", opensInNewTab: "(se deschide într-o filă nouă)" },
  },
};
