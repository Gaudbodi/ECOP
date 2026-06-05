import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../../hooks/useTheme'
import { cn } from '../../lib/cn'

/**
 * ThemeToggle — replaces the 🌓 emoji button at
 * ghana_cap_dashboard.html:382-384 with lucide-react icons.
 *
 * The icon shown is the *target* state (Sun while dark, Moon while light)
 * so the button reads as "click to switch to <icon>".
 */
export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme()
  const Icon = theme === 'dark' ? Sun : Moon
  return (
    <button
      type="button"
      onClick={toggle}
      title="Toggle Light/Dark Mode"
      aria-label="Toggle Light/Dark Mode"
      className={cn(
        'inline-flex h-9 w-9 items-center justify-center rounded-full',
        'border border-white/10 bg-white/5 hover:bg-white/10 transition-colors',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-400',
        className,
      )}
    >
      <Icon className="h-4 w-4" />
      <span className="sr-only">Toggle theme</span>
    </button>
  )
}
