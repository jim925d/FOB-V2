export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['DM Serif Display', 'Georgia', 'serif'],
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        'fob-accent': '#3ECF8E',
        'fob-copper': '#C8956A',
        'fob-info': '#60A5FA',
        'fob-warn': '#F5A623',
        'fob-purple': '#A855F7',
        'fob-orange': '#E08A52',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
