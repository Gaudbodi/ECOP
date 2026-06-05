import { ChevronDown, CheckCircle2, TrendingUp } from 'lucide-react'
import type { CapAlert } from '../../api/types'
import { StageBadge } from '../ui/StageBadge'
import { SeverityBadge } from '../ui/SeverityBadge'
import { cn } from '../../lib/cn'

interface AlertSummaryProps {
  alert: CapAlert
  expanded: boolean
}

/**
 * AlertSummary — collapsed-card top row.
 *
 * Ports ghana_cap_dashboard.html:401-415:
 *   StageBadge | headline (large) | sent + affected_regions | SeverityBadge | chevron
 *
 * The chevron rotates 180° when expanded. `truncate` on the headline +
 * sub-line keeps the row a single line on narrow screens.
 */
export function AlertSummary({ alert, expanded }: AlertSummaryProps) {
  return (
    <div className="flex items-center justify-between gap-4 p-5">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <StageBadge stage={alert.workflow_stage} />
          {alert.lifecycle === 'extended' && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-mono uppercase tracking-[0.18em] bg-rose-500/15 text-rose-200 border border-rose-400/30">
              <TrendingUp className="h-3 w-3" />
              Extended{(alert.extension_count ?? 0) > 1 ? ` ×${alert.extension_count}` : ''}
            </span>
          )}
          {alert.lifecycle === 'terminated' && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-mono uppercase tracking-[0.18em] bg-emerald-500/15 text-emerald-200 border border-emerald-400/30">
              <CheckCircle2 className="h-3 w-3" />
              Resolved
            </span>
          )}
          <span className="text-[10px] font-mono uppercase tracking-[0.22em] text-white/45">
            {alert.identifier}
          </span>
        </div>
        <div className="font-semibold text-lg sm:text-xl leading-snug truncate">{alert.headline}</div>
        <div className="flex items-center gap-2 mt-1 text-xs text-white/55 flex-wrap">
          <span className="font-mono">{alert.sent}</span>
          <span className="text-white/30">·</span>
          <span>{alert.affected_regions.join(', ') || 'Ghana (General)'}</span>
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        <SeverityBadge severity={alert.severity} />
        <ChevronDown
          className={cn('h-5 w-5 transition-transform text-white/60', expanded && 'rotate-180')}
        />
      </div>
    </div>
  )
}
