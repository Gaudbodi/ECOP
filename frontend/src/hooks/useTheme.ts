import { useCallback, useEffect, useState } from 'react'

export type Theme = 'light' | 'dark'

/**
 * Read the initial theme from localStorage. Defaults to `'dark'` to match
 * the existing Jinja behavior at ghana_cap_dashboard.html:543:
 *
 *     const savedTheme = localStorage.getItem('theme') || 'dark';
 *
 * The no-flash bootstrap in frontend/index.html runs the same logic before
 * React mounts; this initializer just keeps React state in sync with what
 * the painted DOM already shows.
 */
function readInitial(): Theme {
  if (typeof window === 'undefined') return 'dark'
  try {
    return window.localStorage.getItem('theme') === 'light' ? 'light' : 'dark'
  } catch {
    // Private mode / disabled storage — fall back to dark default.
    return 'dark'
  }
}

/**
 * useTheme — port of ghana_cap_dashboard.html:533-544 toggleTheme().
 *
 * - Reads / writes `localStorage.theme` ('light' | 'dark').
 * - Applies `data-theme` attribute on BOTH <html> and <body> (matches the
 *   existing Jinja behavior plus the no-flash bootstrap in index.html).
 * - Drops the `updateGlobeColors(newTheme)` call from the original — that
 *   coupling lives in Phase 7's globe component (PATTERNS.md "What to
 *   change" under useTheme).
 */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(readInitial)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    document.body.setAttribute('data-theme', theme)
    try {
      window.localStorage.setItem('theme', theme)
    } catch {
      /* private mode / disabled storage — UI still toggles in-memory */
    }
  }, [theme])

  const toggle = useCallback(() => {
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'))
  }, [])

  return { theme, setTheme, toggle }
}
