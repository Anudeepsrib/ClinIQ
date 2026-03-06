import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "var(--background)",
                foreground: "var(--foreground)",
                border: "var(--border)",
                navy: {
                    900: "#0a192f",
                    800: "#112240",
                    700: "#233554",
                },
                cyan: {
                    400: "#64ffda",
                    500: "#00b4d8",
                    600: "#0096c7",
                },
                gold: {
                    400: "#fae178", // Lighter variant
                    500: "#f8d858", // Base logo color RGB: 248, 216, 88
                    600: "#d6b638", // Darker variant for hover
                },
                red: {
                    500: "#ef233c",
                    600: "#d90429",
                },
            },
            borderRadius: {
                none: "0",
                sm: "0.125rem",
                md: "0.125rem", // Strict 2px rounding
                lg: "0.125rem",
                full: "9999px",
            },
            fontFamily: {
                sans: ["var(--font-inter)", "sans-serif"],
                mono: ["var(--font-roboto-mono)", "monospace"],
                display: ["var(--font-inter-display)", "sans-serif"],
            },
        },
    },
    plugins: [],
};
export default config;
