import { GlassCard } from '../ui/GlassCard'
import { ThemeToggle } from './ThemeToggle'
import { TabNav, type TabId } from './TabNav'
import type { User } from '../../api/types'

interface NavbarProps {
  user: User | null
  loadingUser: boolean
  activeTab: TabId
  onTabChange: (tab: TabId) => void
}

/**
 * Navbar — port of ghana_cap_dashboard.html:372-391.
 *
 * Contract:
 * - Brand text "GHANA CAP" with the existing sky-to-purple gradient.
 * - Three tabs (Pipeline / Manual Entry / Settings) — Manual Entry hidden
 *   for cap validator role per the Jinja gate at line 376.
 * - Theme toggle (lucide Sun/Moon, replacing the 🌓 emoji).
 * - User name + role + agency, or skeleton placeholders while loading.
 * - Logout link to GET /logout (Flask owns the route at ghana_cap_app.py:196).
 *
 * The parent (App.tsx) fetches /api/v1/me once and passes user down — do NOT
 * have Navbar re-fetch (would multiply identical calls per-render under
 * StrictMode and during tab switches).
 */
export function Navbar({ user, loadingUser, activeTab, onTabChange }: NavbarProps) {
  return (
    <GlassCard
      variant="navbar"
      className="sticky top-0 z-30 flex items-center justify-between px-6 py-3 rounded-none"
    >
      {/* Brand — gradient text + status dot */}
      <div className="flex items-center gap-3">
        <div className="relative w-2.5 h-2.5">
          <span className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-75" />
          <span className="absolute inset-0 rounded-full bg-emerald-400" />
        </div>
        <div className="leading-tight">
          <div className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-sky-300 via-cyan-200 to-purple-300 bg-clip-text text-transparent">
            GHANA CAP
          </div>
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-white/50">
            National Emergency Nexus
          </div>
        </div>
      </div>

      <TabNav active={activeTab} onChange={onTabChange} userRole={user?.role} />

      <div className="flex items-center gap-4">
        <ThemeToggle />

        <div className="text-right min-w-[10rem]">
          {loadingUser ? (
            <>
              <div className="h-3 w-24 ml-auto rounded bg-white/10 animate-pulse mb-1" />
              <div className="h-2.5 w-16 ml-auto rounded bg-white/5 animate-pulse" />
            </>
          ) : user ? (
            <>
              <div className="font-semibold text-sm">{user.name}</div>
              <div className="text-xs text-white/60">
                {user.role} ({user.agency})
              </div>
            </>
          ) : (
            <div className="text-xs text-red-300">Session expired — refresh to log in</div>
          )}
        </div>

        <a
          href="/logout"
          className="px-3 py-2 rounded-lg text-sm font-semibold bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors"
        >
          Logout
        </a>
      </div>
    </GlassCard>
  )
}
