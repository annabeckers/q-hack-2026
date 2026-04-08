import { useState, useEffect, useCallback } from "react";

type Theme = "dark" | "light";

const STORAGE_KEY = "theme-preference";

const THEMES: Record<Theme, Record<string, string>> = {
  dark: {
    "--bg-primary": "#0a0a0a",
    "--bg-secondary": "#1a1a1a",
    "--bg-tertiary": "#2a2a2a",
    "--text-primary": "#fafafa",
    "--text-secondary": "#a3a3a3",
    "--text-muted": "#525252",
    "--border": "#333",
  },
  light: {
    "--bg-primary": "#fafafa",
    "--bg-secondary": "#f0f0f0",
    "--bg-tertiary": "#e5e5e5",
    "--text-primary": "#0a0a0a",
    "--text-secondary": "#525252",
    "--text-muted": "#a3a3a3",
    "--border": "#d4d4d4",
  },
};

function getInitialTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "dark" || stored === "light") return stored;
  return "dark";
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  const vars = THEMES[theme];
  for (const [prop, value] of Object.entries(vars)) {
    root.style.setProperty(prop, value);
  }
}

export default function DarkModeToggle() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  return (
    <button
      onClick={toggle}
      title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      style={{
        padding: "6px 10px",
        borderRadius: 8,
        border: "1px solid #333",
        background: "transparent",
        color: "#fafafa",
        cursor: "pointer",
        fontSize: 16,
        lineHeight: 1,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {theme === "dark" ? "\u2600\uFE0F" : "\u{1F319}"}
    </button>
  );
}
