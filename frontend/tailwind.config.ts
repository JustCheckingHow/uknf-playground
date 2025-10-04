import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#004b8d',
          foreground: '#ffffff'
        },
        accent: {
          DEFAULT: '#ffb703',
          foreground: '#1b1b1b'
        }
      }
    }
  },
  plugins: []
};

export default config;
