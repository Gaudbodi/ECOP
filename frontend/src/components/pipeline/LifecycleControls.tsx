import { useState } from 'react'
import { CheckCircle2, TrendingUp } from 'lucide-react'
import type { CapAlert, Role } from '../../api/types'
import { ApiError } from '../../api/client'
import { extendAlert, terminateAlert } from '../../api/alerts'
import { TerminateDialog, ExtendDialog } from './LifecycleDialogs'

const LIFECYCLE_ROLES: Role[] = ['cap validator', 'Admin', 'Super Admin']

interface LifecycleControlsProps {
  alert: CapAlert
  userRole: Role | undefined
}

/**
 * LifecycleControls — Terminate + Extend buttons for a dispatched alert.
 *
 * Visibility rules:
 *   - workflow_stage must be 3 (dispatched).
 *   - userRole must be cap validator, Admin, or Super Admin.
 *   - Terminated alerts hide both buttons (no further lifecycle actions).
 *
 * Server-side reconciliation: both endpoints emit `alert_updated` over
 * Socket.IO. `useAlerts` patches the list, so we DO NOT mutate state here.
 */
export function LifecycleControls({ alert, userRole }: LifecycleControlsProps) {
  const [terminateOpen, setTerminateOpen] = useState(false)
  const [extendOpen, setExtendOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const canActOnLifecycle =
    !!userRole && LIFECYCLE_ROLES.includes(userRole) && alert.workflow_stage === 3
  if (!canActOnLifecycle) return null
  if (alert.lifecycle === 'terminated') {
    return (
      <div
        className="mt-4 pt-4 border-t border-white/10 text-xs text-white/55"
        onClick={(e) => e.stopPropagation()}
      >
        Resolved by{' '}
        <span className="font-semibold text-white/80">{alert.terminated_by ?? '—'}</span>{' '}
        on <span className="font-mono">{alert.terminated_at}</span>
        {alert.terminated_reason && (
          <>
            {' · '}
            <span className="italic">“{alert.terminated_reason}”</span>
          </>
        )}
      </div>
    )
  }

  async function onTerminate(reason: string) {
    setSubmitting(true)
    setError(null)
    try {
      await terminateAlert(alert.identifier, reason)
      setTerminateOpen(false)
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, { error: String(e) }))
    } finally {
      setSubmitting(false)
    }
  }

  async function onExtend(payload: {
    reason: string
    severity?: CapAlert['severity']
    appended_description?: string
  }) {
    setSubmitting(true)
    setError(null)
    try {
      await extendAlert(alert.identifier, payload)
      setExtendOpen(false)
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, { error: String(e) }))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-white/10"
      onClick={(e) => e.stopPropagation()}
    >
      <span className="text-[10px] font-mono uppercase tracking-[0.22em] text-white/45 mr-1">
        Lifecycle
      </span>
      <button
        type="button"
        onClick={() => setExtendOpen(true)}
        disabled={submitting}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-400/30 bg-rose-500/10 text-rose-100 text-xs font-semibold uppercase tracking-wide hover:bg-rose-500/20 disabled:opacity-50"
      >
        <TrendingUp className="h-3.5 w-3.5" />
        {alert.lifecycle === 'extended' ? `Extend again (×${alert.extension_count ?? 1})` : 'Extend / worsening'}
      </button>
      <button
        type="button"
        onClick={() => setTerminateOpen(true)}
        disabled={submitting}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-400/30 bg-emerald-500/10 text-emerald-100 text-xs font-semibold uppercase tracking-wide hover:bg-emerald-500/20 disabled:opacity-50"
      >
        <CheckCircle2 className="h-3.5 w-3.5" />
        Terminate / resolved
      </button>
      {alert.lifecycle === 'extended' && alert.extended_at && (
        <span className="text-[11px] text-white/55 ml-1">
          Last updated <span className="font-mono">{alert.extended_at}</span>
          {alert.extension_reason && (
            <>
              {' · '}
              <span className="italic">“{alert.extension_reason}”</span>
            </>
          )}
        </span>
      )}
      {error && (
        <div role="alert" className="w-full text-xs text-red-300 mt-1">
          Lifecycle action failed: {error.message}
        </div>
      )}

      <TerminateDialog
        open={terminateOpen}
        alertHeadline={alert.headline}
        submitting={submitting}
        onCancel={() => setTerminateOpen(false)}
        onSubmit={onTerminate}
      />
      <ExtendDialog
        open={extendOpen}
        alertHeadline={alert.headline}
        currentSeverity={alert.severity}
        submitting={submitting}
        onCancel={() => setExtendOpen(false)}
        onSubmit={onExtend}
      />
    </div>
  )
}
