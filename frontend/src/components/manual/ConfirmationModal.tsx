import { useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { MapPanel } from './MapPanel'
import type { MapTarget } from './MapPanel'
import type { Severity, Urgency } from '../../api/types'
import { SeverityBadge } from '../ui/SeverityBadge'

export interface ConfirmationPayload {
  headline: string
  description: string
  instruction: string
  severity: Severity
  urgency: Urgency
  location: string
  radius_km: number
  target: MapTarget
}

interface ConfirmationModalProps {
  open: boolean
  payload: ConfirmationPayload | null
  onCancel: () => void
  onConfirm: () => void
  submitting: boolean
}

export function ConfirmationModal({
  open,
  payload,
  onCancel,
  onConfirm,
  submitting,
}: ConfirmationModalProps) {
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && !submitting) onCancel()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, submitting, onCancel])

  return (
    <AnimatePresence>
      {open && payload && (
        <motion.div
          key="overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="cap-overlay fixed inset-0 flex items-center justify-center bg-slate-950/70 backdrop-blur-md p-4"
          onClick={() => !submitting && onCancel()}
        >
          <motion.div
            key="modal"
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.96 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="glass-card w-full max-w-5xl max-h-[92vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="confirm-title"
          >
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <p className="text-xs font-mono uppercase tracking-[0.2em] text-sky-300/80 mb-1">
                  Pre-dispatch review
                </p>
                <h2 id="confirm-title" className="text-3xl font-bold leading-tight">
                  {payload.headline || 'Untitled alert'}
                </h2>
              </div>
              <SeverityBadge severity={payload.severity} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
              <div className="lg:col-span-3">
                <MapPanel
                  visible
                  readonly
                  target={payload.target}
                  onLocationChange={() => undefined}
                  className="w-full h-[360px] rounded-2xl overflow-hidden border border-white/15"
                />
                <div className="mt-3 flex flex-wrap gap-2 text-xs font-mono">
                  <span className="px-2 py-1 rounded-md bg-white/5 border border-white/10">
                    {payload.target.label}
                  </span>
                  <span className="px-2 py-1 rounded-md bg-white/5 border border-white/10">
                    {payload.target.lat.toFixed(4)}, {payload.target.lon.toFixed(4)}
                  </span>
                  <span className="px-2 py-1 rounded-md bg-sky-500/15 border border-sky-400/30 text-sky-200">
                    radius {payload.target.radius_km} km
                  </span>
                  <span className="px-2 py-1 rounded-md bg-purple-500/15 border border-purple-400/30 text-purple-200 capitalize">
                    {payload.target.event_type} overlay
                  </span>
                </div>
              </div>

              <div className="lg:col-span-2 space-y-4 text-sm">
                <Section label="Description" body={payload.description} />
                <Section
                  label="Public instructions"
                  body={payload.instruction || '— none —'}
                />
                <div className="grid grid-cols-2 gap-3">
                  <KV label="Severity" value={payload.severity} />
                  <KV label="Urgency" value={payload.urgency} />
                </div>
                <div className="rounded-xl border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs text-amber-100">
                  Confirming will translate this alert (English → Twi + Hausa),
                  generate audio for each language, dispatch to the MNO
                  webhook, and broadcast to the public TV display.
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 justify-end mt-6">
              <button
                type="button"
                onClick={onCancel}
                disabled={submitting}
                className="px-4 py-2.5 rounded-xl border border-white/15 text-sm font-semibold hover:bg-white/5 disabled:opacity-50"
              >
                Back to edit
              </button>
              <button
                type="button"
                onClick={onConfirm}
                disabled={submitting}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 via-cyan-400 to-purple-500 text-slate-950 text-sm font-bold uppercase tracking-wide shadow-lg shadow-sky-500/30 disabled:opacity-50"
              >
                {submitting ? 'Dispatching…' : 'Confirm & dispatch'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function Section({ label, body }: { label: string; body: string }) {
  return (
    <div>
      <div className="text-[11px] font-mono uppercase tracking-[0.2em] text-white/55 mb-1">
        {label}
      </div>
      <div className="text-white/85 leading-relaxed">{body}</div>
    </div>
  )
}

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-white/55">
        {label}
      </div>
      <div className="text-sm font-semibold mt-0.5">{value}</div>
    </div>
  )
}
