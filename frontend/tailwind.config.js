/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef8ff",
          100: "#d9efff",
          200: "#bce2ff",
          300: "#8ecdff",
          400: "#58b0fc",
          500: "#3192f6",
          600: "#1a75eb",
          700: "#135fd7",
          800: "#164eac",
          900: "#174388",
        },
      },
    },
  },
  plugins: [],
}
