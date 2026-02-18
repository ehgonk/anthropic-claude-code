/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg:     'rgb(var(--color-bg) / <alpha-value>)',
          card:   'rgb(var(--color-card) / <alpha-value>)',
          border: 'rgb(var(--color-border) / <alpha-value>)',
          text:   'rgb(var(--color-text) / <alpha-value>)',
          muted:  'rgb(var(--color-muted) / <alpha-value>)',
        },
        green: {
          profit: '#26a69a',
        },
        red: {
          loss: '#ef5350',
        },
      },
    },
  },
  plugins: [],
}
