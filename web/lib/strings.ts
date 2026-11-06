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
} as const;
