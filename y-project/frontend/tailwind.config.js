/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef9ff",
          100: "#d8f1ff",
          200: "#b9e7ff",
          300: "#89d9ff",
          400: "#51c2ff",
          500: "#29a3ff",
          600: "#1184f7",
          700: "#0a6de3",
          800: "#0f57b8",
          900: "#134b91",
          950: "#112f58",
        },
        gain: "#10b981",
        loss: "#ef4444",
        neutral: "#6b7280",
      },
    },
  },
  plugins: [],
};
