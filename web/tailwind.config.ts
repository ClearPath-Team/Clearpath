import type { Config } from "tailwindcss";

// Design tokens from the approved redesign (M4-08, #28). Radius and shadow scales
// are replaced, not extended, so components can't drift from the design.
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    borderRadius: {
      none: "0",
      sm: "2px",
      DEFAULT: "4px",
      full: "9999px",
    },
    boxShadow: {
      none: "none",
      hairline: "0 0 0 1px #D2D2D7",
      "inset-hairline": "inset 0 0 0 1px #D2D2D7",
    },
    extend: {
      colors: {
        ink: { DEFAULT: "#1D1D1F", secondary: "#6E6E73", tertiary: "#424245" },
        surface: "#F5F5F7",
        hairline: "#D2D2D7",
        // 4.51:1 on white: use on white or under white text, never as text on gray.
        accent: { DEFAULT: "#0076DF", hover: "#0062BA" },
        link: { DEFAULT: "#0066CC", hover: "#004C99" },
        critical: { DEFAULT: "#D70015", bg: "#FDECEE" },
        serious: { DEFAULT: "#B25000", bg: "#FDF1E6" },
        moderate: { DEFAULT: "#4B49D0", bg: "#EFEFFD" },
        minor: { DEFAULT: "#5E5E63", bg: "#F1F1F3" },
        highlight: "#FFD700",
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", '"SF Pro Text"', "Inter", '"Segoe UI"', "sans-serif"],
        mono: ["ui-monospace", '"SF Mono"', "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
