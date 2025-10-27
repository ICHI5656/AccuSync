import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // AccuSync カラーパレット（ソフトグリーン基調）
        accent: '#6bb89c',
        ink: '#203036',
        muted: '#5b6b72',
        line: '#e7efea',
      },
    },
  },
  plugins: [],
}
export default config
