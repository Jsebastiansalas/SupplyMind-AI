/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0c0d10",
        surface: "#121316",
        surfaceRaised: "#18191e",
        charcoal: {
          950: "#090a0c",
          900: "#0f1013",
          850: "#141519",
          800: "#1a1b21",
          750: "#22232b",
          700: "#2b2c36",
          600: "#3d3e4c",
          500: "#5a5c6e",
          400: "#898b9f",
        },
        gold: {
          300: "#eed98d",
          400: "#dfc15d",
          500: "#d4af37",
          600: "#b99528",
          700: "#8a6e1a",
          900: "rgba(212, 175, 55, 0.14)",
          950: "rgba(212, 175, 55, 0.07)",
        },
        card: "#141519",
        cardBorder: "#23252c",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        serif: ['Georgia', 'Cambria', 'serif'],
      },
      boxShadow: {
        'subtle': '0 1px 3px rgba(0, 0, 0, 0.35)',
        'elevated': '0 8px 24px -4px rgba(0, 0, 0, 0.65)',
        'gold-glow': '0 0 16px -2px rgba(212, 175, 55, 0.15)',
      },
    },
  },
  plugins: [],
}
