import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import type { CapAlert, Role } from '../../api/types'
import { AlertSummary } from './AlertSummary'
import { AlertDetail } from './AlertDetail'

interface AlertCardProps {
  alert: CapAlert
  userRole: Role | undefined
}

/**
 * AlertCard — wrapper with framer-motion expand/collapse.
 *
 * Replaces the CSS `max-height: 500px` kludge from ghana_cap_dashboard.html:156
 * (PATTERNS.md "AlertCard.tsx" — the kludge clips long descriptions; framer-
 * motion `height: 0 → 'auto'` measures correctly).
 *
 * The card itself is the click target (role="button") for accessibility;
 * Enter / Space toggle. The expanded detail uses e.stopPropagation() on its
 * own onClick so clicks inside the detail (text selection, audio controls,
 * validator buttons) don't toggle expand/collapse.
 *
 * `motion/react` is the canonical post-rebrand import — never `framer-motion`.
 */
export function AlertCard({ alert, userRole }: AlertCardProps) {
  const [expanded, setExpanded] = useState(false)
  return (
    <motion.div
      layout
      className="glass-item overflow-hidden hover:-translate-y-0.5 hover:shadow-lg cursor-pointer"
      onClick={() => setExpanded((e) => !e)}
      role="button"
      aria-expanded={expanded}
      tabIndex={0}
      onKeyDown={(e) => {
        // Only toggle when the card div itself is focused. Keydown events
        // BUBBLE from descendants — including the lifecycle <dialog>s'
        // textareas — so without this guard, typing a space/Enter into the
        // Terminate reason collapses the card, unmounting LifecycleControls
        // and tearing down the open dialog mid-flow.
        if (e.target !== e.currentTarget) return
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          setExpanded((s) => !s)
        }
      }}
    >
      <AlertSummary alert={alert} expanded={expanded} />
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="detail"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()} /* clicks inside detail don't toggle expand */
          >
            <AlertDetail alert={alert} userRole={userRole} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
