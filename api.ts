/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        night: "#0B0A12",
        panel: "#131118",
        line: "#262230",
        ivory: "#EDE8DA",
        muted: "#8E8798",
        violet: "#8A79D6",
        coral: "#E0684B",
        teal: "#2FBFA0",
        danger: "#E05C5C",
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        body: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
