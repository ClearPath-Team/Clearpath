# Product Overview

## What is ClearPath?

ClearPath is a web application that makes visible and audible how a blind user navigates any website with assistive screen-reading technology. The user inputs a webpage URL, and an automated agent launches the page inside a headless Chromium instance. The agent inspects the page element-by-element and performs sequential keyboard Tab traversal. From this walkthrough, ClearPath renders a narrated video where each active element is visually highlighted in synchronization with the spoken screen reader announcement. Simultaneously, an automated accessibility audit (axe-core) flags accessibility violations. Each issue is linked to the exact second in the video clip where it is encountered. The final output features the video, an organized list of issues, an overall score from 0 to 100, and actionable recommendations.

**Input:** A public URL. **Output:** `clip.mp4` + `report.json`, displayed in an interactive dashboard.

## User Journey

1. The user inputs a target URL and clicks "Analizează" (Analyze).
2. The user watches real-time progress across 4 pipeline stages: preparation, page extraction, analysis, and video rendering.
3. The user arrives at the results dashboard: video player, numeric accessibility score, and categorized issue list.
4. Clicking an issue jumps the video player directly to the second where that element is spoken and highlighted.
5. The user can copy and share the unique analysis link with teammates or stakeholders.

## In Scope for MVP

- Single webpage analysis per run (public URL, no authentication required).
- Short video clip of at most ~90 seconds (capped at 40 spoken announcements).
- Sequential Tab traversal with automated keyboard trap detection.
- axe-core accessibility audit, numeric 0–100 score, and actionable recommendation templates.
- Interactive results page with video player, synchronized issue list, and shareable link.

## Out of Scope for MVP

- User accounts, authentication, or saved history.
- Multi-page user flows (e.g., product page → shopping cart → multi-step checkout).
- Real-time comparison against desktop NVDA binaries.
- Cloud storage integration (all files reside locally in `data/`).
- Real-time LLM-generated recommendations (kept as an optional stretch goal if time permits).
