/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#020617",
        surface: "#0f172a",
        card: "rgba(30, 41, 59, 0.4)",
        cardHover: "rgba(30, 41, 59, 0.7)",
        borderGlow: "rgba(56, 189, 248, 0.3)",
        neonCyan: "#38bdf8",
        neonIndigo: "#818cf8",
        neonEmerald: "#10b981",
        neonCrimson: "#ef4444",
        neonAmber: "#f59e0b",
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'neon-cyan': '0 0 20px -3px rgba(56, 189, 248, 0.35)',
        'neon-indigo': '0 0 20px -3px rgba(129, 140, 248, 0.35)',
        'neon-emerald': '0 0 20px -3px rgba(16, 185, 129, 0.35)',
        'neon-crimson': '0 0 20px -3px rgba(239, 68, 68, 0.35)',
        'glass': '0 10px 30px -10px rgba(0, 0, 0, 0.5)',
      },
      backdropBlur: {
        'xs': '2px',
      }
    },
  },
  plugins: [],
}
