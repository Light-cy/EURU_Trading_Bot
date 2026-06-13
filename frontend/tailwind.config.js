/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0F172A",
        card: "#1E293B",
        text: "#F8FAFC",
        success: "#22C55E",
        danger: "#EF4444",
        primary: "#3B82F6",
        border: "#334155"
      }
    },
  },
  plugins: [],
}
