/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0b0e",
        surface: "#101116",
        surfaceRaised: "#15161c",
        charcoal: {
          950: "#07080a",
          900: "#0c0d11",
          850: "#111217",
          800: "#161820",
          750: "#1d1f28",
          700: "#242733",
          600: "#363a4b",
          500: "#52576d",
          400: "#7c829e",
          300: "#a6accc",
        },
        gold: {
          300: "#f0df9e",
          400: "#e4ca6f",
          500: "#d4af37",
          600: "#b59328",
          700: "#8c6f1a",
          900: "rgba(212, 175, 55, 0.12)",
          950: "rgba(212, 175, 55, 0.05)",
        },
        slateBorder: "#1e2029",
        card: "#111217",
        cardBorder: "#1e2029",
        cardHoverBorder: "#2d303e",
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Consolas', 'Fira Code', 'monospace'],
        serif: ['Georgia', 'Cambria', 'serif'],
      },
      boxShadow: {
        'subtle': '0 1px 2px rgba(0, 0, 0, 0.4)',
        'elevated': '0 6px 20px -3px rgba(0, 0, 0, 0.7)',
        'modal': '0 24px 48px -12px rgba(0, 0, 0, 0.85)',
        'tactile': '0 1px 0 rgba(255, 255, 255, 0.05) inset',
      },
    },
  },
  plugins: [],
}

