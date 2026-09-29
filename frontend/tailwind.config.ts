import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        outfit: ['var(--font-outfit)', 'sans-serif'],
        inter: ['var(--font-inter)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      colors: {
        background: '#000000',
        surface: '#0A0A0A',
        border: '#222222',
        accent: {
          DEFAULT: '#F59E0B',
          hover: '#D97706',
        },
        text: {
          primary: '#F8FAFC',
          secondary: '#94A3B8',
        },
        success: '#10B981',
        danger: '#EF4444',
      },
    },
  },
  plugins: [],
};

export default config;
