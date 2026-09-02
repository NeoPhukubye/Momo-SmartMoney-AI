/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        mtn: {
          yellow: '#FFCC00',
          blue: '#003087',
          dark: '#1A1A2E',
          light: '#F5F5F7',
        },
      },
      fontSize: {
        'a11y-sm': '0.9rem',
        'a11y-base': '1.1rem',
        'a11y-lg': '1.3rem',
        'a11y-xl': '1.6rem',
      },
    },
  },
  plugins: [],
}
