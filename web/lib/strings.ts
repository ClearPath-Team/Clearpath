// Interface copy, kept in one place so a Romanian version can be added (M4-04, #38).
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
    lead: "ClearPath navigates your page with the keyboard only, reads it aloud like a Romanian screen reader, and shows every issue in a narrated video.",
    urlLabel: "Web address to analyze",
    submit: "Analyze",
    submitting: "Starting…",
    hint: "Usually under 3 minutes. One page, no sign-in.",
    tryDemo: "Try the demo page:",
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
          title: "We read it aloud in Romanian",
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
} as const;
