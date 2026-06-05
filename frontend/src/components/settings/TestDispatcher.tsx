import { useState } from 'react'
import { Zap } from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { testDispatch } from '../../api/system'
import { ApiError } from '../../api/client'
import type { Role } from '../../api/types'

/**
 * TestDispatcher — Admin-only button that POSTs to /api/v1/dispatcher/test.
 *
 * UI gate matches the server gate (Plan 04-01 added a 403 for non-Admin).
 * Per PATTERNS.md "Role gate", the UI gate is UX-only — defense-in-depth.
 * For non-Admin we render an explanatory placeholder instead of a disabled
 * button, since a disabled button invites confused click attempts.
 *
 * On success, the resulting alert appears in Pipeline via Socket.IO
 * `new_alert`; this component shows the new identifier inline so the
 * operator can correlate without leaving the Settings tab.
 */

interface TestDispatcherProps {
  userRole: Role | undefined
}

export function TestDispatcher({ userRole }: TestDispatcherProps) {
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (userRole !== 'Admin') {
    return (
      <GlassCard variant="card">
        <h3 className="text-lg font-bold mb-2">Test Dispatcher</h3>
        <p className="text-sm text-white/60">
          Available to Admin role only.
        </p>
      </GlassCard>
    )
  }

  async function run() {
    if (submitting) return
    setSubmitting(true)
    setResult(null)
    setError(null)
    try {
      const res = await testDispatch()
      setResult(
        `Mock alert dispatched: ${res.identifier}. Check the Pipeline tab.`,
      )
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? `${err.status}: ${
              (err.payload as { error?: string } | null)?.error ?? 'Test dispatch failed'
            }`
          : String(err)
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <GlassCard variant="card" className="space-y-3">
      <h3 className="text-lg font-bold">Test Dispatcher</h3>
      <p className="text-sm text-white/70">
        Inject a synthetic GMeT payload through the full ingest → enrich →
        dispatch pipeline. Useful for verifying end-to-end without waiting
        for a real weather event.
      </p>
      <button
        type="button"
        onClick={run}
        disabled={submitting}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-sky-500/20 hover:bg-sky-500/30 border border-sky-500/40 text-sm font-bold uppercase tracking-wide disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Zap className="h-4 w-4" />
        {submitting ? 'Dispatching…' : 'Run Test Dispatch'}
      </button>
      {result && (
        <div
          role="status"
          className="text-sm text-emerald-200 p-2 rounded-md bg-emerald-500/10 border border-emerald-500/30"
        >
          {result}
        </div>
      )}
      {error && (
        <div
          role="alert"
          className="text-sm text-red-200 p-2 rounded-md bg-red-500/10 border border-red-500/30"
        >
          {error}
        </div>
      )}
    </GlassCard>
  )
}
