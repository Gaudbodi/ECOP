import { useState } from 'react'
import { motion } from 'motion/react'
import { GlassCard } from '../ui/GlassCard'
import { ManualEntryForm } from './ManualEntryForm'
import { MapPanel } from './MapPanel'
import type { MapTarget } from './MapPanel'

/**
 * ManualEntry — Phase-5/6 redesigned manual alert flow.
 *
 * Three columns of the experience:
 *   1. Form (left)        — headline, location, radius (optional), severity,
 *                           urgency, description, instruction.
 *   2. Live map (right)   — shows the resolved affected area: marker, radius
 *                           circle, alert-type animation overlay.
 *   3. Confirmation modal — opened by "Review & dispatch", repeats the same
 *                           map at high zoom + the alert summary.
 *
 * The agent endpoint `/api/v1/agents/area` does the geocode + radius
 * inference. The map is read from `target` state owned here so the form,
 * the live map, and the confirmation modal all stay in sync.
 */
export function ManualEntry() {
  const [target, setTarget] = useState<MapTarget | null>(null)

  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >
        <p className="text-xs font-mono uppercase tracking-[0.22em] text-sky-300/80 mb-1">
          Compose
        </p>
        <h2 className="text-3xl sm:text-4xl font-bold leading-tight">
          Generate a CAP alert
        </h2>
        <p className="text-sm text-white/60 mt-1 max-w-2xl">
          Describe the event, name the location, and let the agent draw the
          affected area. Review the zoomed map + animation before the alert
          leaves the building.
        </p>
      </motion.div>

      <GlassCard className="p-5 sm:p-7">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3">
            <ManualEntryForm
              onTargetChange={setTarget}
              onSubmitted={() => setTarget(null)}
            />
          </div>

          <div className="lg:col-span-2">
            <div className="text-[11px] font-mono uppercase tracking-[0.22em] text-white/60 mb-2">
              Affected area preview
            </div>
            <MapPanel
              visible
              target={target}
              onLocationChange={() => undefined}
              className="w-full h-[480px] rounded-2xl overflow-hidden border border-white/15"
            />
            <p className="text-xs text-white/55 mt-2 leading-relaxed">
              {target ? (
                <>
                  <span className="text-emerald-300">●</span> Resolved.
                  The radius circle and event animation reflect the agent's
                  current best guess. Override the radius field and press
                  Resolve again to refine.
                </>
              ) : (
                <>
                  <span className="text-amber-300">●</span> Not yet resolved.
                  Fill in the form and press <strong>Resolve affected area</strong>
                  {' '}— the map flies to the location, draws a circle for the
                  radius, and overlays an animation matching the alert type.
                </>
              )}
            </p>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}
