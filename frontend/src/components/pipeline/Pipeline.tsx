import { useState } from 'react'
import { Map as MapIcon } from 'lucide-react'
import { useAlerts } from '../../hooks/useAlerts'
import type { User } from '../../api/types'
import { GlassCard } from '../ui/GlassCard'
import { AlertCard } from './AlertCard'
import { LiveEventsMap } from './LiveEventsMap'

interface PipelineProps {
  user: User | null
}

/**
 * Pipeline — top-level Pipeline tab.
 *
 * Reads `useAlerts` and renders the five UI states explicitly:
 *
 *   1. degraded   — yellow banner + (potentially empty) list
 *   2. error      — red banner + retry hint (if not also degraded)
 *   3. loading    — spinner-text while initial fetch in flight + list empty
 *   4. empty      — informational empty-state once load settles with no alerts
 *   5. list       — AlertCard per alert, keyed by identifier
 *
 * The `degraded` and `error` banners can co-exist with the list (e.g. cached
 * socket-pushed alerts despite Mongo being down), so they're rendered
 * independently of the list state.
 */
export function Pipeline({ user }: PipelineProps) {
  const { alerts, loading, error, degraded } = useAlerts()
  const [mapOpen, setMapOpen] = useState(false)

  // Active = dispatched AND not terminated. Extended alerts still count as active.
  const active = alerts.filter(
    (a) => a.workflow_stage === 3 && a.lifecycle !== 'terminated',
  ).length
  const resolved = alerts.filter((a) => a.lifecycle === 'terminated').length
  const pending = alerts.filter((a) => a.workflow_stage === 1).length
  const drafts = alerts.filter((a) => a.workflow_stage === 0).length

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <p className="text-xs font-mono uppercase tracking-[0.22em] text-sky-300/80 mb-1">
            Live operations
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold leading-tight">
            Alerts workflow pipeline
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setMapOpen(true)}
          disabled={active === 0}
          className="group inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-sky-400/40 bg-sky-500/10 text-sm font-semibold text-sky-100 hover:bg-sky-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <MapIcon className="h-4 w-4" />
          View live events on map
          <span className="ml-1 font-mono text-xs px-1.5 py-0.5 rounded-md bg-sky-400/20 border border-sky-400/30 tabular-nums">
            {active}
          </span>
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <Stat label="Total" value={alerts.length} accent="sky" />
        <Stat label="Active" value={active} accent="emerald" />
        <Stat label="Pending" value={pending} accent="amber" />
        <Stat label="Resolved" value={resolved} accent="violet" />
        <Stat label="Draft / rejected" value={drafts} accent="rose" />
      </div>

      <GlassCard className="p-5 sm:p-6">

      {degraded && (
        <div
          role="alert"
          className="mb-4 p-3 rounded-md bg-amber-500/10 border border-amber-500/30 text-sm text-amber-200"
        >
          Datastore unavailable — showing live Socket.IO updates only. Refresh to retry.
        </div>
      )}

      {error && !degraded && (
        <div
          role="alert"
          className="mb-4 p-3 rounded-md bg-red-500/10 border border-red-500/30 text-sm text-red-200"
        >
          Failed to load alerts: {error.message}
        </div>
      )}

      {loading && alerts.length === 0 && (
        <div className="text-sm text-white/60 py-8 text-center">Loading alerts…</div>
      )}

      {!loading && alerts.length === 0 && (
        <div className="text-sm text-white/60 py-8 text-center">
          No alerts yet. New alerts appear here in real time.
        </div>
      )}

      <div className="space-y-3">
        {alerts.map((a) => (
          <AlertCard key={a.identifier} alert={a} userRole={user?.role} />
        ))}
      </div>
      </GlassCard>

      <LiveEventsMap
        alerts={alerts}
        open={mapOpen}
        onClose={() => setMapOpen(false)}
      />
    </div>
  )
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string
  value: number
  accent: 'sky' | 'emerald' | 'amber' | 'rose' | 'violet'
}) {
  const ring =
    accent === 'sky'
      ? 'border-sky-400/30 from-sky-400/15'
      : accent === 'emerald'
        ? 'border-emerald-400/30 from-emerald-400/15'
        : accent === 'amber'
          ? 'border-amber-400/30 from-amber-400/15'
          : accent === 'violet'
            ? 'border-violet-400/30 from-violet-400/15'
            : 'border-rose-400/30 from-rose-400/15'
  return (
    <div
      className={`relative rounded-2xl border ${ring} bg-gradient-to-br to-transparent backdrop-blur px-4 py-3`}
    >
      <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-white/55">
        {label}
      </div>
      <div className="text-3xl font-bold tabular-nums leading-none mt-1">{value}</div>
    </div>
  )
}
