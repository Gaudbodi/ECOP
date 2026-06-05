import { useState } from 'react'
import { useValidation } from '../../hooks/useValidation'
import { RejectDialog } from '../ui/RejectDialog'
import type { CapAlert, Role } from '../../api/types'

interface ValidatorControlsProps {
  alert: CapAlert
  userRole: Role | undefined
}

/**
 * ValidatorControls — port of the role + stage gate from
 * ghana_cap_dashboard.html:437-442. Wraps RejectDialog for the reject path.
 *
 * IMPORTANT — rules-of-hooks ordering: `useValidation()` and `useState()`
 * MUST be called BEFORE the `if (!canValidate) return null` early return.
 * Calling hooks after the early return is a violation of React's rules-of-
 * hooks: when `workflow_stage` flips 1 -> 3 mid-session (which is exactly
 * what happens during validator approve), the hook call count would change
 * across renders and React throws "Rendered more hooks than during the
 * previous render". The plan's W7 revision flagged this.
 */
export function ValidatorControls({ alert, userRole }: ValidatorControlsProps) {
  // Hooks first — unconditional.
  const { approve, reject, submitting, error } = useValidation()
  const [rejectOpen, setRejectOpen] = useState(false)

  // Gate matches ghana_cap_dashboard.html:437 verbatim. Computed AFTER hooks
  // so a stage transition does not change the hook call count.
  const canValidate =
    (userRole === 'cap validator' || userRole === 'Admin') &&
    alert.workflow_stage === 1
  if (!canValidate) return null

  return (
    <div
      className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-white/10"
      onClick={(e) => e.stopPropagation()} /* don't bubble into AlertCard expand toggle */
    >
      <button
        type="button"
        onClick={() => void approve(alert.identifier)}
        disabled={submitting}
        className="px-4 py-2 rounded-md bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-sm font-bold uppercase tracking-wide disabled:opacity-50"
      >
        {submitting ? 'Processing…' : 'Approve & Dispatch'}
      </button>
      <button
        type="button"
        onClick={() => setRejectOpen(true)}
        disabled={submitting}
        className="px-4 py-2 rounded-md bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-sm font-bold uppercase tracking-wide disabled:opacity-50"
      >
        Reject
      </button>

      <RejectDialog
        open={rejectOpen}
        submitting={submitting}
        onCancel={() => setRejectOpen(false)}
        onSubmit={async (reason) => {
          try {
            await reject(alert.identifier, reason)
            setRejectOpen(false)
          } catch {
            // useValidation surfaces error in `error`; keep dialog open so
            // the user can retry / amend the reason.
          }
        }}
      />

      {error && (
        <div role="alert" className="w-full text-sm text-red-300 mt-1">
          Validation failed: {error.message}
        </div>
      )}
    </div>
  )
}
