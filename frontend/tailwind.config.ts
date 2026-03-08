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
                    900: "#050505", // Stark Black
                    800: "#171717", // Neutral 900
                    700: "#262626", // Neutral 800
                },
                cyan: {
                    400: "#64ffda",
                    500: "#00b4d8",
                    600: "#0096c7",
                },
                gold: {
                    400: "#ffeb85",
                    500: "#ffde59", // Exact Logo Color RGB: 255, 222, 89
                    600: "#cca82a",
                },
                crimson: {
                    500: "#b81d1d",
                    600: "#8f1818", // Exact Logo Red RGB: 143, 24, 24
                },
                red: {
                    500: "#ef233c",
                    600: "#d90429",
                },
            },
            borderRadius: {
                none: "0px",
                sm: "0px",
                md: "2px", // Strict Enterprise rounding
                lg: "2px",
                xl: "2px",
                "2xl": "2px",
                "3xl": "2px",
                full: "9999px",
            },
            fontFamily: {
                sans: ["var(--font-source-sans)", "sans-serif"],
                display: ["var(--font-lexend)", "sans-serif"],
                mono: ["var(--font-roboto-mono)", "monospace"],
            },
        },
    },
    plugins: [],
};
export default config;
