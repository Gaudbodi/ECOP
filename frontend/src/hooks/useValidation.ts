import { useCallback, useState } from 'react'
import { validateAlert } from '../api/alerts'
import { ApiError } from '../api/client'

export interface UseValidationState {
  approve: (identifier: string) => Promise<void>
  reject: (identifier: string, reason: string) => Promise<void>
  submitting: boolean
  error: ApiError | null
  lastSuccess: { identifier: string; action: 'approve' | 'reject' } | null
}

/**
 * useValidation — wraps POST /api/v1/alerts/validate/<id> with submit state.
 *
 * Critical: this hook does NOT mutate `useAlerts` state on success. The
 * server's `validate_alert` handler emits `alert_updated` on the default
 * Socket.IO namespace (ghana_cap_app.py:370); `useAlerts` subscribes and
 * reconciles. Manually mutating here would race the socket event and
 * reintroduce the latency the migration is removing.
 *
 * Errors are re-thrown so callers (e.g. RejectDialog's submit handler) can
 * choose to keep their UI open on failure — the hook surfaces the error in
 * `error` for inline display and also throws so the caller can branch.
 */
export function useValidation(): UseValidationState {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)
  const [lastSuccess, setLastSuccess] = useState<UseValidationState['lastSuccess']>(null)

  const run = useCallback(
    async (identifier: string, action: 'approve' | 'reject', reason?: string) => {
      setSubmitting(true)
      setError(null)
      try {
        await validateAlert(identifier, action, reason)
        setLastSuccess({ identifier, action })
        // No state mutation here — Plan 01's validate_alert emits
        // `alert_updated` on success, and useAlerts subscribes.
      } catch (e) {
        const apiErr = e instanceof ApiError ? e : new ApiError(0, { error: String(e) })
        setError(apiErr)
        throw apiErr
      } finally {
        setSubmitting(false)
      }
    },
    [],
  )

  const approve = useCallback((identifier: string) => run(identifier, 'approve'), [run])
  const reject = useCallback(
    (identifier: string, reason: string) => run(identifier, 'reject', reason),
    [run],
  )

  return { approve, reject, submitting, error, lastSuccess }
}
