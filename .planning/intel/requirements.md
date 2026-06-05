# Requirements (PRD Intel)

> Extracted per-requirement from PRD.txt (Ghana CAP Platform E2E Test). One entry per requirement. PRD scope is narrower than SPEC — it is the GMeT-only PoC milestone of the broader E-CoP. See INGEST-CONFLICTS.md INFO bucket.

---

## Ingress

### REQ-gmet-webhook-endpoint
- source: PRD.txt §3.1
- description: Expose a secure POST endpoint for GMeT webhook ingress.
- acceptance:
  - endpoint path: `/api/v1/alerts/gmet/webhook`
  - HTTP method: POST
  - System receives a valid JSON POST request at the GMeT webhook URL (PRD §6 acceptance #1)
- scope: GMeT → platform ingress

### REQ-gmet-webhook-auth
- source: PRD.txt §3.1
- description: Authenticate GMeT webhook calls.
- acceptance:
  - Require API key OR Bearer token validation
- scope: GMeT → platform ingress security

### REQ-cap-payload-parsing
- source: PRD.txt §3.1, §2 step 2
- description: Parse incoming CAP v1.2 payload.
- acceptance:
  - Extract elements: `identifier`, `sender`, `sent`, `status`, `msgType`, `scope`, `info` (category, event, urgency, severity, certainty, headline, description, area)
  - Validate against CAP v1.2 standards
  - Map to internal data structures
- scope: CAP processing module

## Enrichment

### REQ-geo-resolution
- source: PRD.txt §3.2 ("Geo-Boundary Service"), §6 acceptance #2
- description: Resolve incoming coordinates / polygons / circles to Ghanaian administrative areas.
- acceptance:
  - Inputs accepted: GeoJSON polygon, GeoJSON circle, manual graphical polygon drawing, administrative-level selection
  - Output: array of localized strings, e.g. `["Greater Accra Region", "Accra Metropolitan"]`
  - System accurately identifies the Ghanaian district/region based on coordinates in the payload
- scope: enrichment / geo-spatial resolution

### REQ-translation
- source: PRD.txt §3.2 ("Translation Service"), §6 acceptance #3
- description: Translate the English alert text into local language variants.
- acceptance:
  - Minimum viable PoC languages: English, Twi, Hausa
  - Implementation may use a translation API or local LLM service
  - Alert text is successfully translated into at least one local language variant
- scope: enrichment / translation
- note: PRD §2 step 4 also lists Ga and Ewe as targets; only Twi/Hausa are required for PoC acceptance.

### REQ-tts
- source: PRD.txt §3.2 ("TTS Service"), §6 acceptance #4
- description: Convert translated and English text into audio files.
- acceptance:
  - Output formats: MP3 / WAV
  - Audio stored in cloud bucket OR local temporary storage
  - Returns an accessible URL per audio file
  - TTS engine generates a playable audio link for the alert
- scope: enrichment / TTS

## Dispatch

### REQ-mno-webhook-dispatch
- source: PRD.txt §3.3 ("MNO Webhook Push"), §2 step 6 Target A, §6 acceptance #5
- description: Push the fully enriched alert payload to the configured MNO endpoint.
- acceptance:
  - Construct outbound JSON payload containing processed text, geo-data, and media links
  - Execute POST to the configured MNO test URL
  - Retry logic: exponential backoff on failed deliveries
  - **MNO webhook endpoint receives the fully enriched JSON payload within 5 seconds of the initial GMeT trigger**
- scope: dispatch / MNO

### REQ-sms-dispatch
- source: PRD.txt §3.3 ("SMS API Integration"), §2 step 6 Target B, §6 acceptance #6
- description: Send concise text-only SMS to pre-registered test phone numbers.
- acceptance:
  - Extract highest-priority translated text (default to English)
  - Map mapped administrative areas to a dummy database of test phone numbers
  - Trigger SMS via an SMS API provider
  - Pre-registered test mobile numbers receive an SMS containing the alert text
- scope: dispatch / SMS
- note: SMS gateway candidates per §5: Africa's Talking or Twilio. Current implementation uses Twilio (CLAUDE.md §Services).

## Persistence & Logging

### REQ-event-logging
- source: PRD.txt §6 acceptance #7
- description: Persist all pipeline events to the database for later analysis.
- acceptance:
  - All events properly logged in the database
- scope: observability / audit
- note: PRD §5 specifies MongoDB; CLAUDE.md confirms this is implemented via `db.save_alert` upsert by `identifier`.

## Admin Dashboard (UI)

### REQ-dashboard-active-alerts-view
- source: PRD.txt §4 ("Active Alerts")
- description: Provide an alert lifecycle view for operators.
- acceptance:
  - Kanban-style OR list view
  - Pipeline statuses visible: Received → Processing → Translated → Dispatched
- scope: admin UI

### REQ-dashboard-webhook-config
- source: PRD.txt §4 ("Webhook Config")
- description: Allow operators to generate and manage webhook URL and API keys.
- acceptance:
  - Screen to generate Webhook URL
  - Screen to manage API keys for GMeT
- scope: admin UI

### REQ-dashboard-test-dispatcher
- source: PRD.txt §4 ("Test Dispatcher")
- description: Provide a manual trigger for injecting mock GMeT JSON.
- acceptance:
  - Manual trigger button injects a mock GMeT JSON payload
  - Tests the flow without waiting for a real weather event
- scope: admin UI / testing

### REQ-design-language-glassmorphism
- source: PRD.txt §4 ("Design Language")
- description: Adhere to glassmorphism design language across the dashboard.
- acceptance:
  - Semi-transparent backgrounds with background blur
  - Subtle light borders
  - Distinct drop shadows
  - Layered modern aesthetic over a clean dark-mode-friendly background
- scope: admin UI / visual design
