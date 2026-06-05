// Source of truth: ghana_cap_app.py:387-412 (process_alert_logic) and
// services/enrichment_service.py:98-135 (translations dict shape).
//
// These types mirror the Mongo `alerts` document shape and the JSON envelopes
// produced by the Phase 4 endpoints in ghana_cap_app.py. Do NOT drift —
// the React app trusts these as the server's contract; runtime validation
// (zod) is intentionally deferred (RESEARCH.md "Don't Hand-Roll").

export type WorkflowStage = 0 | 1 | 3
// 0 = Rejected/Draft, 1 = Pending Validation, 3 = Dispatched.
// No `2` — verified against ghana_cap_app.py and CLAUDE.md state machine.

export type Severity = 'Extreme' | 'Severe' | 'Moderate' | 'Minor' | 'Unknown'
export type Urgency = 'Immediate' | 'Expected' | 'Future' | 'Past' | 'Unknown'
export type Certainty = 'Observed' | 'Likely' | 'Possible' | 'Unlikely' | 'Unknown'
export type Category =
  | 'Met'
  | 'Geo'
  | 'Safety'
  | 'Security'
  | 'Rescue'
  | 'Fire'
  | 'Health'
  | 'Env'
  | 'Transport'
  | 'Infra'
  | 'CBRNE'
  | 'Other'
export type CapStatus = 'Actual' | 'Exercise' | 'System' | 'Test' | 'Draft'
export type CapMsgType = 'Alert' | 'Update' | 'Cancel' | 'Ack' | 'Error'
export type CapScope = 'Public' | 'Restricted' | 'Private'
export type Role = 'Super Admin' | 'Admin' | 'cap generator' | 'cap validator'

export type Lifecycle = 'active' | 'extended' | 'terminated'

export interface LifecycleHistoryEntry {
  action: 'extend' | 'terminate'
  by: string
  by_email?: string
  by_role?: string
  at: string
  reason: string
  severity_before?: Severity
  severity_after?: Severity
}

export interface CapAlert {
  identifier: string
  sender_name: string
  sender_agency: string
  sender_id: string
  sender_ip: string
  sent: string
  status: CapStatus
  msgType: CapMsgType
  scope: CapScope
  category: Category
  event: string
  urgency: Urgency
  severity: Severity
  certainty: Certainty
  headline: string
  description: string
  instruction: string
  affected_regions: string[]
  translations: Record<string, string>
  audio_links: Record<string, string>
  geo: { lat: number; lon: number }
  mno_dispatched: boolean
  sms_sent: boolean
  workflow_stage: WorkflowStage
  validated_by?: string
  validated_at?: string
  rejected_by?: string
  rejected_reason?: string
  // Lifecycle (terminate / extend) — added on top of workflow_stage so
  // a stage-3 dispatched alert can additionally be 'extended' or
  // 'terminated' without changing its dispatched status.
  lifecycle?: Lifecycle
  lifecycle_history?: LifecycleHistoryEntry[]
  terminated_by?: string
  terminated_at?: string
  terminated_reason?: string
  extended_by?: string
  extended_at?: string
  extension_reason?: string
  extension_count?: number
  // Mongo internal — stringified by Plan 01's GET /api/v1/alerts. Optional
  // because forms / sockets may surface alerts before persistence.
  _id?: string
}

export interface User {
  staff_id: string
  name: string
  agency: string
  role: Role
  email: string
  phone_number?: string | null
  created_at?: string
  created_by?: string
  is_superuser?: boolean
}

export interface Stakeholder {
  id: string
  name: string
  scope: string
  color: string
}

export interface NewUserPayload {
  email: string
  name: string
  agency: string
  role: 'Admin' | 'cap generator' | 'cap validator'
  phone_number?: string
  staff_id?: string
}

export interface AlertsListResponse {
  alerts: CapAlert[]
  degraded: boolean
  error?: string
}

export interface ManualAlertRequest {
  headline: string
  severity: Severity
  urgency: Urgency
  description: string
  instruction: string
  latitude: number | string
  longitude: number | string
  // Optional CAP fields with server-side defaults.
  category?: Category
  event?: string
  certainty?: Certainty
}

export interface ValidationRequest {
  action: 'approve' | 'reject'
  reason?: string
}

export interface DispatchSuccessResponse {
  status: 'success'
  identifier: string
  message: string
}

export interface ApiErrorResponse {
  error: string
}

// Plan 06's agent draft endpoint shape — defined here so Plan 04's
// Manual Entry tab can import without circular Plan dependency.
// See ghana_cap_app.py:340-354.
export interface AgentDraftResponse {
  headline: string
  description: string
  instruction: string
  severity: Severity
  urgency: Urgency
  category?: Category
}
