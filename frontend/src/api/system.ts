// Typed wrappers for system-level endpoints (Settings tab, future health
// probes, etc). Kept separate from `api/alerts.ts` so the alerts surface
// stays focused on the alert lifecycle.

import { apiFetch } from './client'
import type { DispatchSuccessResponse } from './types'

/**
 * POST /api/v1/dispatcher/test
 * Admin-only Test Dispatcher (added in Plan 04-01). Server uses a
 * fixed mock GMeT-shaped payload (`_TEST_DISPATCHER_MOCK_PAYLOAD`)
 * and runs it through `process_alert_logic` at workflow_stage=3 so
 * the synthetic alert traces the full ingest → enrich → dispatch
 * path and surfaces in Pipeline via the `new_alert` socket emit.
 *
 * Body is intentionally empty — the GMeT API key never reaches the
 * browser; the server constructs the payload internally and posts
 * to MNO/Twilio via the existing dispatch_service singletons.
 *
 * Returns 403 for non-Admin (defense-in-depth; the UI also gates).
 */
export function testDispatch(): Promise<DispatchSuccessResponse> {
  return apiFetch<DispatchSuccessResponse>('/api/v1/dispatcher/test', {
    method: 'POST',
  })
}
