import { useCallback, useEffect, useState } from 'react'
import { fetchAlerts } from '../api/alerts'
import { socket } from '../api/socket'
import { ApiError } from '../api/client'
import type { CapAlert } from '../api/types'

export interface UseAlertsState {
  alerts: CapAlert[]
  loading: boolean
  error: ApiError | null
  degraded: boolean
  refetch: () => Promise<void>
  // Internal helpers used by useAlerts itself for socket-event reconciliation
  // (new_alert prepend, alert_updated patch). NOT advertised as a public API
  // for outside consumers — Pipeline reconciliation is server-driven via the
  // Socket.IO `new_alert` / `alert_updated` events, not callable methods.
  addAlert: (a: CapAlert) => void
  updateAlert: (identifier: string, patch: Partial<CapAlert>) => void
}

/**
 * useAlerts — initial GET /api/v1/alerts + Socket.IO subscription.
 *
 * Replaces the legacy full-page-reload reconciliation pattern at
 * ghana_cap_dashboard.html:669-673. Server-side semantics:
 *
 *  - `new_alert` is emitted by `process_alert_logic` after every upsert
 *    (ghana_cap_app.py). Re-emission of the same `identifier` should
 *    REPLACE, not duplicate, the existing entry — so the prepend dedups
 *    by identifier.
 *  - `alert_updated` is emitted by `validate_alert` on approve
 *    (ghana_cap_app.py:370). The hook patches the matching entry in place.
 *
 * Cleanup is wired in the effect's return so React 19 StrictMode's
 * double-mount doesn't leak socket listeners.
 */
export function useAlerts(): UseAlertsState {
  const [alerts, setAlerts] = useState<CapAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<ApiError | null>(null)
  const [degraded, setDegraded] = useState(false)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchAlerts()
      setAlerts(res.alerts)
      setDegraded(res.degraded)
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, { error: String(e) }))
      setAlerts([])
      setDegraded(false)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refetch()
  }, [refetch])

  // Socket.IO subscription — replaces the legacy reload hack at
  // ghana_cap_dashboard.html:669-673.
  useEffect(() => {
    function onNew(a: CapAlert) {
      // Dedup by identifier (process_alert_logic upserts; a re-emission of
      // the same identifier should replace, not duplicate, the existing
      // entry).
      setAlerts((prev) => [a, ...prev.filter((x) => x.identifier !== a.identifier)])
    }
    function onUpdated(a: CapAlert) {
      setAlerts((prev) => prev.map((x) => (x.identifier === a.identifier ? a : x)))
    }
    socket.on('new_alert', onNew)
    socket.on('alert_updated', onUpdated)
    return () => {
      socket.off('new_alert', onNew)
      socket.off('alert_updated', onUpdated)
    }
  }, [])

  const addAlert = useCallback((a: CapAlert) => {
    setAlerts((prev) => [a, ...prev.filter((x) => x.identifier !== a.identifier)])
  }, [])

  const updateAlert = useCallback((identifier: string, patch: Partial<CapAlert>) => {
    setAlerts((prev) => prev.map((x) => (x.identifier === identifier ? { ...x, ...patch } : x)))
  }, [])

  return { alerts, loading, error, degraded, refetch, addAlert, updateAlert }
}
