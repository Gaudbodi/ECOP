import type { CapAlert } from '../../api/types'

interface DispatchStatusProps {
  alert: Pick<CapAlert, 'workflow_stage' | 'mno_dispatched' | 'sms_sent'>
}

// Ports the MNO + SMS status block from ghana_cap_dashboard.html:427-434.
// Phase 7 will add public-feed broadcast confirmation
// (REQ-pipeline-detail-dispatch-status); Phase 4 ships MNO + SMS only since
// that's what the enriched_alert document carries today.

function statusLabel(value: boolean, stage: 0 | 1 | 3): string {
  if (value) return 'Sent'
  if (stage === 1) return 'Pending'
  return 'Failed'
}

function statusIcon(value: boolean, stage: 0 | 1 | 3): string {
  if (value) return '✅'
  if (stage === 1) return '⏳'
  return '❌'
}

export function DispatchStatus({ alert }: DispatchStatusProps) {
  return (
    <div className="space-y-1 text-sm">
      <div>
        <span className="font-semibold text-white/80">Stage:</span>{' '}
        <span className="font-mono">{alert.workflow_stage}</span>
      </div>
      <div>
        <span className="font-semibold text-white/80">MNO:</span>{' '}
        {statusIcon(alert.mno_dispatched, alert.workflow_stage)}{' '}
        {statusLabel(alert.mno_dispatched, alert.workflow_stage)}
      </div>
      <div>
        <span className="font-semibold text-white/80">SMS:</span>{' '}
        {statusIcon(alert.sms_sent, alert.workflow_stage)}{' '}
        {statusLabel(alert.sms_sent, alert.workflow_stage)}
      </div>
    </div>
  )
}
