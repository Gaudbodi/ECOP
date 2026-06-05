import type { WorkflowStage } from '../../api/types'
import { cn } from '../../lib/cn'

interface StageBadgeProps {
  stage: WorkflowStage
  className?: string
}

// Maps WorkflowStage (0 / 1 / 3) to the human-readable label and the
// red / amber / emerald color triplet defined in
// ghana_cap_dashboard.html:189-198 (.stage-1 orange, .stage-3 green,
// .stage-0 red) and the inline label at :404-405.
//
// CLAUDE.md state machine: stages are 0 / 1 / 3 only — no `2`.
const stageMeta: Record<WorkflowStage, { label: string; classes: string }> = {
  0: { label: 'Draft/Rejected', classes: 'bg-red-500/20 text-red-300 border-red-500/40' },
  1: { label: 'Pending Review', classes: 'bg-amber-500/20 text-amber-300 border-amber-500/40' },
  3: { label: 'Dispatched', classes: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' },
}

export function StageBadge({ stage, className }: StageBadgeProps) {
  const meta = stageMeta[stage] ?? stageMeta[0]
  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wide border',
        meta.classes,
        className,
      )}
    >
      {meta.label}
    </span>
  )
}
