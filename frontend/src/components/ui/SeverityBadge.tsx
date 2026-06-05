import type { Severity } from '../../api/types'
import { cn } from '../../lib/cn'

interface SeverityBadgeProps {
  severity: Severity | string
  className?: string
}

/**
 * Map a CAP severity value to a Tailwind background class.
 *
 * Ports the substring-match logic from public_feed.html:294-301 — defensive
 * against arbitrary casing / unknown values. Color hex values come from
 * public_feed.html:111-115 verbatim so the React badge is pixel-identical
 * to the existing public feed badge.
 */
function severityColor(sev: string): string {
  const s = (sev ?? '').toLowerCase()
  if (s.includes('extreme')) return 'bg-[#b91c1c] text-white'
  if (s.includes('severe')) return 'bg-[#ea580c] text-white'
  if (s.includes('moderate')) return 'bg-[#ca8a04] text-white'
  if (s.includes('minor')) return 'bg-[#16a34a] text-white'
  return 'bg-gradient-to-br from-sky-500 to-purple-500 text-white'
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wide',
        severityColor(severity),
        className,
      )}
    >
      {severity || 'Unknown'}
    </span>
  )
}
