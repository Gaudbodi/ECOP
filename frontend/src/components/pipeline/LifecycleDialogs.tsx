import { useEffect, useRef, useState } from 'react'
import { GlassCard } from '../ui/GlassCard'
import type { Severity } from '../../api/types'

const SEVERITIES: Severity[] = ['Extreme', 'Severe', 'Moderate', 'Minor']

interface TerminateDialogProps {
  open: boolean
  alertHeadline: string
  submitting?: boolean
  onCancel: () => void
  onSubmit: (reason: string) => Promise<void> | void
}

/**
 * TerminateDialog — confirm + capture a reason before ending a dispatched
 * alert. The CAP semantics emitted server-side are msgType=Cancel.
 */
export function TerminateDialog({
  open,
  alertHeadline,
  submitting,
  onCancel,
  onSubmit,
}: TerminateDialogProps) {
  const [reason, setReason] = useState('')
  const ref = useRef<HTMLDialogElement>(null)
  const wasOpen = useRef(false)

  useEffect(() => {
    if (!ref.current) return
    if (open) {
      if (!ref.current.open) ref.current.showModal()
      // Reset the typed reason ONLY on the closed→open edge — never on a
      // benign re-render while the dialog is already open. This keeps a
      // half-typed CAP Cancel reason intact when background socket traffic
      // re-renders the surrounding tree.
      if (!wasOpen.current) setReason('')
    } else if (ref.current.open) {
      ref.current.close()
    }
    wasOpen.current = open
  }, [open])

  return (
    <dialog
      ref={ref}
      // Close path is EXPLICIT user intent only: the native cancel/Esc event
      // (preventDefault → onCancel), the Cancel button (onCancel), and a
      // successful submit (onSubmit). No outside-click / blur / focus-loss
      // close handler exists, so transient re-renders never drop the dialog.
      onCancel={(e) => {
        e.preventDefault()
        onCancel()
      }}
      className="bg-transparent text-white p-0 backdrop:bg-black/60"
    >
      <GlassCard variant="card" className="w-[30rem] max-w-[90vw]">
        <p className="text-[11px] font-mono uppercase tracking-[0.2em] text-amber-300/80 mb-1">
          End active alert · CAP Cancel
        </p>
        <h3 className="text-lg font-bold mb-3 leading-snug">
          Terminate “{alertHeadline}”?
        </h3>
        <p className="text-xs text-white/65 mb-3 leading-relaxed">
          The alert will be marked as resolved and removed from the live
          events map. A CAP Cancel message is broadcast to the public feed
          and MNO subscribers.
        </p>
        <label className="block text-xs font-mono uppercase tracking-[0.18em] text-white/60 mb-1.5" htmlFor="terminate-reason">
          Resolution reason (required)
        </label>
        <textarea
          id="terminate-reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          className="w-full rounded-xl bg-slate-900/40 border border-white/15 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400/60"
          placeholder="e.g. Fire contained by GFRS; no further risk."
        />
        <div className="flex gap-2 justify-end mt-4">
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="px-3 py-2 rounded-xl border border-white/15 text-sm font-semibold hover:bg-white/5 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => reason.trim() && void onSubmit(reason.trim())}
            disabled={submitting || !reason.trim()}
            className="px-4 py-2 rounded-xl border border-amber-400/40 bg-amber-400/15 text-amber-100 text-sm font-bold uppercase tracking-wide disabled:opacity-50"
          >
            {submitting ? 'Terminating…' : 'Terminate alert'}
          </button>
        </div>
      </GlassCard>
    </dialog>
  )
}

interface ExtendDialogProps {
  open: boolean
  alertHeadline: string
  currentSeverity: Severity
  submitting?: boolean
  onCancel: () => void
  onSubmit: (payload: {
    reason: string
    severity?: Severity
    appended_description?: string
  }) => Promise<void> | void
}

/**
 * ExtendDialog — reason + optional severity bump + appended note. CAP
 * semantics emitted server-side: msgType=Update, lifecycle=extended.
 */
export function ExtendDialog({
  open,
  alertHeadline,
  currentSeverity,
  submitting,
  onCancel,
  onSubmit,
}: ExtendDialogProps) {
  const [reason, setReason] = useState('')
  const [severity, setSeverity] = useState<Severity>(currentSeverity)
  const [appended, setAppended] = useState('')
  const ref = useRef<HTMLDialogElement>(null)
  const wasOpen = useRef(false)
  const currentSeverityRef = useRef(currentSeverity)
  currentSeverityRef.current = currentSeverity

  useEffect(() => {
    if (!ref.current) return
    if (open) {
      if (!ref.current.open) ref.current.showModal()
      // Reset form state ONLY on the closed→open edge. `currentSeverity` is
      // read from a ref here (not the effect deps) so a background re-render
      // that swaps the alert object's severity prop while the dialog is open
      // does NOT wipe the in-progress reason / severity choice / appended note.
      if (!wasOpen.current) {
        setReason('')
        setSeverity(currentSeverityRef.current)
        setAppended('')
      }
    } else if (ref.current.open) {
      ref.current.close()
    }
    wasOpen.current = open
  }, [open])

  return (
    <dialog
      ref={ref}
      // Close path is EXPLICIT user intent only: the native cancel/Esc event
      // (preventDefault → onCancel), the Cancel button (onCancel), and a
      // successful submit (onSubmit). No outside-click / blur / focus-loss
      // close handler exists, so transient re-renders never drop the dialog.
      onCancel={(e) => {
        e.preventDefault()
        onCancel()
      }}
      className="bg-transparent text-white p-0 backdrop:bg-black/60"
    >
      <GlassCard variant="card" className="w-[34rem] max-w-[92vw]">
        <p className="text-[11px] font-mono uppercase tracking-[0.2em] text-rose-300/80 mb-1">
          Worsening situation · CAP Update
        </p>
        <h3 className="text-lg font-bold mb-3 leading-snug">
          Extend “{alertHeadline}”
        </h3>
        <p className="text-xs text-white/65 mb-3 leading-relaxed">
          Push a CAP Update message — bump severity if the threat has grown,
          and append fresh detail to the description. Public feed + MNO
          subscribers are re-notified.
        </p>

        <label className="block text-xs font-mono uppercase tracking-[0.18em] text-white/60 mb-1.5" htmlFor="extend-reason">
          What changed? (required)
        </label>
        <textarea
          id="extend-reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          className="w-full rounded-xl bg-slate-900/40 border border-white/15 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400/60"
          placeholder="e.g. Fire jumped the river; consuming buildings in adjacent ward."
        />

        <div className="grid grid-cols-2 gap-3 mt-3">
          <div>
            <label className="block text-xs font-mono uppercase tracking-[0.18em] text-white/60 mb-1.5" htmlFor="extend-severity">
              Severity
            </label>
            <select
              id="extend-severity"
              value={severity}
              onChange={(e) => setSeverity(e.target.value as Severity)}
              className="w-full rounded-xl bg-slate-900/40 border border-white/15 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400/60"
            >
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s === currentSeverity ? `${s} (current)` : s}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end text-xs text-white/55 leading-snug">
            {severity !== currentSeverity ? (
              <span>
                Severity will move{' '}
                <span className="font-semibold text-white/85">{currentSeverity}</span>
                {' → '}
                <span className="font-semibold text-rose-200">{severity}</span>.
              </span>
            ) : (
              <span>Keeping severity at {currentSeverity}.</span>
            )}
          </div>
        </div>

        <label className="block text-xs font-mono uppercase tracking-[0.18em] text-white/60 mb-1.5 mt-3" htmlFor="extend-append">
          Append to description (optional)
        </label>
        <textarea
          id="extend-append"
          value={appended}
          onChange={(e) => setAppended(e.target.value)}
          rows={2}
          className="w-full rounded-xl bg-slate-900/40 border border-white/15 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400/60"
          placeholder="Add public-facing detail; timestamped automatically."
        />

        <div className="flex gap-2 justify-end mt-4">
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="px-3 py-2 rounded-xl border border-white/15 text-sm font-semibold hover:bg-white/5 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() =>
              reason.trim() &&
              void onSubmit({
                reason: reason.trim(),
                severity: severity !== currentSeverity ? severity : undefined,
                appended_description: appended.trim() || undefined,
              })
            }
            disabled={submitting || !reason.trim()}
            className="px-4 py-2 rounded-xl border border-rose-400/40 bg-gradient-to-r from-rose-500/30 to-amber-500/30 text-rose-50 text-sm font-bold uppercase tracking-wide disabled:opacity-50"
          >
            {submitting ? 'Publishing update…' : 'Publish CAP update'}
          </button>
        </div>
      </GlassCard>
    </dialog>
  )
}
