import { useCallback, useEffect, useState } from 'react'
import { apiFetch, ApiError } from '../api/client'

export interface UseApiState<T> {
  data: T | null
  error: ApiError | null
  loading: boolean
  refetch: () => Promise<void>
}

/**
 * useApi — generic GET-fetch hook.
 *
 * Returns `{ data, error, loading, refetch }`. Pass `null` as `path` to skip
 * the fetch entirely (useful for guarded fetches: `useApi(user ? `/x/${user.id}` : null)`).
 *
 * RESEARCH.md "Don't Hand-Roll": TanStack Query is overkill for the four
 * endpoints Phase 4 consumes. If the surface grows past ~6 endpoints with
 * mutations, revisit.
 */
export function useApi<T>(path: string | null): UseApiState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [loading, setLoading] = useState(path !== null)

  const fetchOnce = useCallback(async () => {
    if (path === null) return
    setLoading(true)
    setError(null)
    try {
      const result = await apiFetch<T>(path)
      setData(result)
    } catch (e) {
      if (e instanceof ApiError) setError(e)
      else setError(new ApiError(0, { error: String(e) }))
    } finally {
      setLoading(false)
    }
  }, [path])

  useEffect(() => {
    void fetchOnce()
  }, [fetchOnce])

  return { data, error, loading, refetch: fetchOnce }
}
