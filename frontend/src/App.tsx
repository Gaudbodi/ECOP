import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Navbar } from './components/layout/Navbar'
import { GlobePlaceholder } from './components/layout/GlobePlaceholder'
import { Pipeline } from './components/pipeline/Pipeline'
import { ManualEntry } from './components/manual/ManualEntry'
import { Settings } from './components/settings/Settings'
import { AdminPanel } from './components/admin/AdminPanel'
import { useApi } from './hooks/useApi'
import type { User } from './api/types'
import type { TabId } from './components/layout/TabNav'

/**
 * App — top-level shell.
 *
 * Layers:
 *   GlobePlaceholder (fixed, z-0)
 *   └── Navbar (sticky, z-30)
 *   └── main (z-10) → AnimatePresence(mode="wait") → motion.div(key=tab)
 *       ├── tab='pipeline' → <Pipeline user={user} />
 *       ├── tab='manual'   → <ManualEntry user={user} />
 *       └── tab='settings' → <Settings user={user} />
 *
 * Phase 4 is feature-complete after Plan 04-04: all three tabs render
 * real components. Plan 04-05 handles cutover (kill the Jinja dashboard
 * route) and the manual-verify checkpoint.
 *
 * RESEARCH.md notes:
 *  - import from `motion/react` (canonical post-rebrand) — never from `framer-motion`
 *  - tab state is `useState`, not a router — Phase 4 ships without deep-linkable tabs (A6)
 *  - parent fetches `/api/v1/me` once and passes user down to Navbar + Settings
 */
export default function App() {
  const [tab, setTab] = useState<TabId>('pipeline')
  const { data: user, loading: loadingUser } = useApi<User>('/api/v1/me')

  return (
    <>
      <GlobePlaceholder />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar
          user={user}
          loadingUser={loadingUser}
          activeTab={tab}
          onTabChange={setTab}
        />

        <main className="flex-1 px-6 py-8 max-w-7xl mx-auto w-full">
          <AnimatePresence mode="wait">
            <motion.div
              key={tab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
            >
              {tab === 'pipeline' && <Pipeline user={user} />}
              {tab === 'manual' && <ManualEntry user={user} />}
              {tab === 'admin' && <AdminPanel currentUser={user} />}
              {tab === 'settings' && <Settings user={user} />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </>
  )
}
