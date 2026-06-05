import type { Role } from '../../api/types'
import { cn } from '../../lib/cn'

export type TabId = 'pipeline' | 'manual' | 'admin' | 'settings'

interface TabNavProps {
  active: TabId
  onChange: (tab: TabId) => void
  userRole?: Role
}

interface TabDef {
  id: TabId
  label: string
  // Roles allowed to see this tab. Mirrors ghana_cap_dashboard.html:376
  // ({% if user.role in ['cap generator', 'Admin'] %}). Server still
  // enforces — this is UX gating only (PATTERNS.md "Role gate").
  roles: Role[] | 'all'
}

const TABS: TabDef[] = [
  { id: 'pipeline', label: 'Pipeline', roles: 'all' },
  { id: 'manual', label: 'Manual Entry', roles: ['cap generator', 'Admin', 'Super Admin'] },
  { id: 'admin', label: 'Admin', roles: ['Super Admin'] },
  { id: 'settings', label: 'Settings', roles: 'all' },
]

/**
 * TabNav — three top-level tabs with a role-based hide rule for Manual Entry.
 *
 * - Switching tabs is purely click-driven (PATTERNS.md "Anti-patterns to NOT
 *   Carry Over" — no router in Phase 4 per RESEARCH.md A6).
 * - Keyboard a11y (arrow keys / role=tablist) is intentionally deferred to
 *   Phase 9 — the existing Jinja navbar didn't have it either.
 */
export function TabNav({ active, onChange, userRole }: TabNavProps) {
  const visibleTabs = TABS.filter(
    (t) => t.roles === 'all' || (userRole !== undefined && t.roles.includes(userRole)),
  )
  return (
    <div className="flex items-center gap-1 p-1 rounded-full border border-white/10 bg-white/5 backdrop-blur">
      {visibleTabs.map((t) => (
        <button
          key={t.id}
          type="button"
          onClick={() => onChange(t.id)}
          aria-current={active === t.id ? 'page' : undefined}
          className={cn(
            'relative px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-[0.16em] transition-colors',
            active === t.id
              ? 'text-slate-950'
              : 'text-white/65 hover:text-white',
          )}
        >
          {active === t.id && (
            <span
              aria-hidden="true"
              className="absolute inset-0 rounded-full bg-gradient-to-r from-sky-400 to-cyan-300 shadow-lg shadow-sky-500/30"
            />
          )}
          <span className="relative z-10">{t.label}</span>
        </button>
      ))}
    </div>
  )
}
