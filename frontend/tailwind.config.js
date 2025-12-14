export default {
    content: [
      "./index.html",
      "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
          primary: '#7000ff',
          secondary: '#00c6ff',
          dark: '#1a1a2e',
          light: '#f2f4f8',
        },
        fontFamily: {
          outfit: ['Outfit', 'sans-serif'],
        },
        backdropBlur: {
          xs: '2px',
        }
      },
    },
    plugins: [],
  }