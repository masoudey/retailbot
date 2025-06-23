/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
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
        primary: "#f5f5f7", // Apple light-grey background
        accent: "#0071e3"   // Apple blue accent
      }
    }
  },
  plugins: []
};