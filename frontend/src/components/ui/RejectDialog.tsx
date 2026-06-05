import { useEffect, useRef, useState } from 'react'
import { GlassCard } from './GlassCard'

interface RejectDialogProps {
  open: boolean
  onSubmit: (reason: string) => Promise<void> | void
  onCancel: () => void
  submitting?: boolean
}

/**
 * RejectDialog — modal replacing the legacy browser-prompt for the reject
 * reason (ghana_cap_dashboard.html:648).
 *
 * Uses the native HTML `<dialog>` element via showModal() / close() — no
 * extra dependency, gets the focus trap + Esc-to-close behavior for free.
 * The reason textarea is required (submit button disabled until non-empty).
 *
 * Cancel handler runs on:
 *   - Cancel button click
 *   - Escape key (browser fires `cancel` event on the dialog; we
 *     preventDefault and call onCancel so the parent owns the open state)
 */
export function RejectDialog({ open, onSubmit, onCancel, submitting }: RejectDialogProps) {
  const [reason, setReason] = useState('')
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    if (!ref.current) return
    if (open) {
      if (!ref.current.open) ref.current.showModal()
      setReason('')
    } else if (ref.current.open) {
      ref.current.close()
    }
  }, [open])

  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault()
        onCancel()
      }}
      className="bg-transparent text-white p-0 backdrop:bg-black/60"
    >
      <GlassCard variant="card" className="w-[28rem] max-w-[90vw]">
        <h3 className="text-lg font-bold mb-3">Reject Alert</h3>
        <label className="block text-sm text-white/80 mb-1" htmlFor="reject-reason">
          Reason for rejection (required):
        </label>
        <textarea
          id="reject-reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={4}
          className="w-full rounded-md bg-black/30 border border-white/15 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
          placeholder="e.g. Severity overstated; downgrade and re-submit."
        />
        <div className="flex gap-2 justify-end mt-4">
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="px-3 py-1.5 rounded-md bg-white/5 hover:bg-white/10 border border-white/10 text-sm"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => {
              if (reason.trim()) void onSubmit(reason.trim())
            }}
            disabled={submitting || !reason.trim()}
            className="px-3 py-1.5 rounded-md bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-sm font-semibold disabled:opacity-50"
          >
            {submitting ? 'Rejecting…' : 'Reject Alert'}
          </button>
        </div>
      </GlassCard>
    </dialog>
  )
}
