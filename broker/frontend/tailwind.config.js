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
          bg: '#0a0e14',
          card: '#131722',
          border: '#2a2e39',
          text: '#d1d4dc',
          muted: '#787b86',
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
