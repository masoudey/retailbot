// tailwind.config.cjs
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx,js,jsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Helvetica Neue",
          "Helvetica",
          "Arial",
          "sans-serif"
        ]
      },
      colors: {
        primary:   "#1e293b",
        secondary: "#334155",
        accent:    "#3b82f6",
        muted:     "#64748b",
        text:      "#f1f5f9"
      }
    }
  },
  plugins: []
};