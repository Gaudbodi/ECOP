// Typed wrappers around `apiFetch` for the alerts endpoints.
// Kept thin per RESEARCH.md "Don't Hand-Roll": one helper per endpoint,
// no client class.

import { apiFetch } from './client'
import type {
  AlertsListResponse,
  CapAlert,
  DispatchSuccessResponse,
  ManualAlertRequest,
  Severity,
  ValidationRequest,
} from './types'

/**
 * GET /api/v1/alerts
 * Returns `{alerts, degraded}` envelope from Plan 01's list_alerts handler.
 * `degraded: true` indicates Mongo read failed and the caller should render
 * a "Datastore unavailable" banner instead of an error.
 */
export function fetchAlerts(): Promise<AlertsListResponse> {
  return apiFetch<AlertsListResponse>('/api/v1/alerts')
}

/**
 * POST /api/v1/alerts/validate/<identifier>
 * Validator approves or rejects a stage-1 alert. The server emits
 * `alert_updated` on the default Socket.IO namespace on success
 * (ghana_cap_app.py:370), which `useAlerts` subscribes to — callers
 * should NOT manually patch state after this resolves.
 */
export function validateAlert(
  identifier: string,
  action: 'approve' | 'reject',
  reason?: string,
): Promise<DispatchSuccessResponse> {
  const body: ValidationRequest = reason ? { action, reason } : { action }
  return apiFetch<DispatchSuccessResponse>(
    `/api/v1/alerts/validate/${encodeURIComponent(identifier)}`,
    { method: 'POST', body: JSON.stringify(body) },
  )
}

/**
 * POST /api/v1/alerts/manual
 * Manual CAP draft from a generator/Admin. Server runs the same
 * `process_alert_logic` funnel (geo-resolve, translate, TTS, persist),
 * with `workflow_stage=1` (pending validation) for `cap generator` and
 * `workflow_stage=3` (dispatched) for Admin — gating handled server-side.
 *
 * After this resolves, the server emits `new_alert` over Socket.IO
 * (ghana_cap_app.py process_alert_logic), which `useAlerts` is already
 * subscribed to. Callers should NOT manually patch state — Pipeline
 * reconciliation is server-driven.
 *
 * Empty-string lat/lon are tolerated by `_coord_or_default` on the
 * backend (ghana_cap_app.py:444-455) — defaults to Accra coordinates.
 */
export function submitManualAlert(
  payload: ManualAlertRequest,
): Promise<DispatchSuccessResponse> {
  return apiFetch<DispatchSuccessResponse>('/api/v1/alerts/manual', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export interface AreaResolveRequest {
  location?: string
  description?: string
  radius_km?: number
}

export interface AreaResolveResponse {
  lat: number
  lon: number
  radius_km: number
  radius_source: string
  region: string | null
  district: string | null
  label: string
  event_type: string
  geocoder: string
  /**
   * True when the exact place could not be geocoded and the server fell back
   * to a region centroid (or the national centroid). The point is approximate
   * — the operator should verify/adjust the location and radius on the map.
   */
  approximate?: boolean
}

export interface LifecycleResponse {
  status: 'success'
  message: string
  alert: CapAlert
}

export function terminateAlert(
  identifier: string,
  reason: string,
): Promise<LifecycleResponse> {
  return apiFetch<LifecycleResponse>(
    `/api/v1/alerts/${encodeURIComponent(identifier)}/terminate`,
    { method: 'POST', body: JSON.stringify({ reason }) },
  )
}

export interface ExtendPayload {
  reason: string
  severity?: Severity
  appended_description?: string
}

export function extendAlert(
  identifier: string,
  payload: ExtendPayload,
): Promise<LifecycleResponse> {
  return apiFetch<LifecycleResponse>(
    `/api/v1/alerts/${encodeURIComponent(identifier)}/extend`,
    { method: 'POST', body: JSON.stringify(payload) },
  )
}

/**
 * POST /api/v1/agents/area
 * Asks the server to geocode the alert location and infer a sensible
 * affected-area radius. The Confirmation modal uses the response to render
 * the zoomed map + alert-type animation.
 */
export function resolveAlertArea(
  payload: AreaResolveRequest,
): Promise<AreaResolveResponse> {
  return apiFetch<AreaResolveResponse>('/api/v1/agents/area', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
