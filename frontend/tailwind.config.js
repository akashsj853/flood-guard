/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#07141c',
        lagoon: {
          400: '#54d6bf',
          500: '#19b89f',
          700: '#087f72',
        },
        risk: {
          low: '#55c98a',
          moderate: '#d7b95b',
          high: '#e98b58',
          veryhigh: '#e05b61',
          critical: '#b9364b',
        },
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        sans: ['DM Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
