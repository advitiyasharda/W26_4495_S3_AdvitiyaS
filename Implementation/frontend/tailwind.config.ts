import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#5eead4",
          dark: "#2dd4bf",
        },
        pastel: {
          mint: "#ecfdf5",
          sky: "#e0f2fe",
          lilac: "#f5f3ff",
          peach: "#fff7ed",
          rose: "#fff1f2",
        },
      },
    },
  },
  plugins: [],
};

export default config;
