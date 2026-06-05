// Thin fetch wrapper with `credentials: 'same-origin'` (session cookie auth)
// + JSON content type. CSRF stance per RESEARCH.md A1: JSON endpoints stay
// @csrf.exempt under SameSite=Lax; no token-in-header in v1.

import type { ApiErrorResponse } from './types'

export class ApiError extends Error {
  // Explicit field declarations rather than constructor-parameter properties:
  // tsconfig.app.json sets `erasableSyntaxOnly: true` (TS 5.8+ default), which
  // forbids the `constructor(public foo)` shorthand because it's not a pure
  // type-erasable construct.
  status: number
  payload: ApiErrorResponse | unknown

  constructor(status: number, payload: ApiErrorResponse | unknown) {
    super(`API ${status}: ${JSON.stringify(payload)}`)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: 'same-origin',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  // Detect login redirect: Flask `login_required` returns 302 -> /login.
  // In a fetch context this surfaces as `redirected: true` with a final URL
  // ending in /login. Handle both that and an HTML response (some browsers
  // / proxies may follow but mark the body as text/html).
  if (res.redirected && res.url.endsWith('/login')) {
    window.location.href = '/login'
    throw new ApiError(401, { error: 'Login required' })
  }

  if (!res.ok) {
    let body: ApiErrorResponse | unknown = null
    try {
      body = await res.json()
    } catch {
      /* non-JSON body, leave null */
    }
    throw new ApiError(res.status, body)
  }

  // 204 No Content -> return undefined as T (caller's responsibility to type-check).
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}
