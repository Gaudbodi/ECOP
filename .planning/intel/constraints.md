# Constraints (SPEC Intel)

> Extracted from "Requirements Document for Unified Emergency Communication Platform.pdf" (Document Ref No: RQ_DOC_0). This is the master spec; the Ghana CAP PoC (PRD.txt) is a narrower implementation slice. Each constraint preserves the original FR/NFR identifier from the SPEC.

---

## System-Level Constraints

### CONSTRAINT-system-data-privacy
- source: Requirements Document for Unified Emergency Communication Platform.pdf §3.3 (System Constraints, item i)
- type: nfr
- content: Must adhere to data privacy laws and ensure secure handling of personal info (call logs, location data, etc.)

### CONSTRAINT-system-fault-tolerance
- source: Requirements Document for Unified Emergency Communication Platform.pdf §3.3 (System Constraints, item ii)
- type: nfr
- content: Must be fault-tolerant — high availability, backup power, redundant communication paths.

### CONSTRAINT-system-backwards-compat
- source: Requirements Document for Unified Emergency Communication Platform.pdf §3.3 (System Constraints, item iii)
- type: nfr
- content: Must remain backwards-compatible with older radio technologies (analog HF, trunk radio) in remote areas.

### CONSTRAINT-stakeholder-roles
- source: Requirements Document for Unified Emergency Communication Platform.pdf §2 (Stakeholders & High-Level Needs)
- type: protocol
- content: System serves six stakeholder classes: (1) Government Agencies (MoCD, NADMO), (2) Emergency Services (Police, Fire, Ambulance), (3) Telecommunication Network and Infrastructure Operators & ISPs (TNIO), (4) NGOs and Community-Based Organizations, (5) International Partners (UN, ITU, donors), (6) General Public. Each has distinct trigger/receive/coordinate needs.

### CONSTRAINT-system-perspective
- source: Requirements Document for Unified Emergency Communication Platform.pdf §3.1 (System Perspective)
- type: protocol
- content: Centralized yet distributed system handling three concerns — Triggers (any stakeholder signals an incident; system logs/validates/routes), Alerts (system disseminates over multiple technologies on validated triggers), Coordination (multi-agency portal for real-time data, resource sharing, task coordination).

### CONSTRAINT-system-interfaces
- source: Requirements Document for Unified Emergency Communication Platform.pdf §3.2 (System Interfaces)
- type: api-contract
- content:
  - Telecom Networks: integration via CAP or operator-specific APIs for mass alerts (SMS, cell broadcast) and priority calls
  - Broadcast Media: TV/radio integration for live overrides or ticker messages
  - Legacy Systems: HF/VHF radio networks for remote/hard-to-reach areas or fallback when digital infrastructure fails
  - Emerging Technologies: IoT sensors, AI-based analytics, satellite push to smartphones
  - User Interfaces: web portal for agencies, mobile/radio interface for front-line responders, public-facing alerts via SMS / social media / push notifications

---

## Functional Requirements (FR1.x – FR13.2)

### CONSTRAINT-FR1.1-incident-triggers
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.1.1
- type: protocol
- content: The system shall allow any authorized stakeholder to raise an incident trigger through multiple channels (web portal, mobile app, dedicated phone line, VHF radio dispatch).

### CONSTRAINT-FR1.2-trigger-logging
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.1.1
- type: schema
- content: The system shall log the origin, time, and type of each trigger in a centralized database.

### CONSTRAINT-FR2.1-validation-workflow
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.1.2
- type: protocol
- content: The system shall provide workflow-based approval for triggers before public alerts are issued, if required by policy.

### CONSTRAINT-FR2.2-rbac
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.1.2
- type: protocol
- content: The system shall support role-based authentication so only authorized individuals can escalate a trigger to an official alert.

### CONSTRAINT-FR3.1-multi-channel-dissemination
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.1.3
- type: protocol
- content: The system shall disseminate alerts via multiple channels (SMS, cell broadcast, radio, TV override, social media, digital signage) for maximum reach.

### CONSTRAINT-FR3.2-geo-targeting
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.1.3
- type: protocol
- content: The system shall support geo-targeting to send alerts only to affected regions or districts.

### CONSTRAINT-FR3.3-multi-lingual-accessibility
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.1.3
- type: protocol
- content: The system shall provide multi-lingual options and accessibility features (text-to-speech, sign-language overlays for TV, proximity vibrate/beep alerting systems, remote-operated public/community addressing systems).

### CONSTRAINT-FR4.1-two-way-ack
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.1.4
- type: protocol
- content: For two-way communication, recipients (first responders, local authorities) shall be able to acknowledge alert receipt and provide status updates.

### CONSTRAINT-FR4.2-delivery-tracking
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.1.4
- type: schema
- content: The system shall track read/delivery confirmations (where technology permits) to measure alert reach.

### CONSTRAINT-FR5.1-multi-agency-portal
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.2.5
- type: protocol
- content: The system shall provide a multi-agency portal where dispatchers can assign resources (e.g., ambulances, rescue teams) and view current location data.

### CONSTRAINT-FR5.2-dispatch-integration
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.2.5
- type: api-contract
- content: The system shall integrate with existing police/fire dispatch software where feasible or provide open APIs for third-party integration.

### CONSTRAINT-FR6.1-collaboration-channels
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.2.6
- type: protocol
- content: The system shall include chat, voice, or video conferencing capabilities for multi-agency collaboration, especially during incidents.

### CONSTRAINT-FR6.2-comm-logging
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.2.6
- type: schema
- content: The system shall log all communications for post-incident review and reporting.

### CONSTRAINT-FR7.1-hfvhf-integration
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.3.7
- type: api-contract
- content: The system shall allow operators using HF/VHF or trunk radio systems to send/receive incident data (voice, limited text) to the Unified E-CoP for logging and action.

### CONSTRAINT-FR7.2-radio-recordings
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.3.7
- type: schema
- content: The system shall store recordings or transcripts where possible.

### CONSTRAINT-FR8.1-iot-sensors
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.3.8
- type: api-contract
- content: The system shall interface with IoT-based sensors (flood gauges, seismic sensors, weather stations) to receive automated triggers.

### CONSTRAINT-FR8.2-ai-analytics
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.3.8
- type: protocol
- content: The system shall provide an AI/analytics module that can raise alerts automatically when sensor thresholds or anomaly detections occur (e.g., when river level exceeds a safe limit).

### CONSTRAINT-FR9.1-satellite
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.3.9
- type: api-contract
- content: The system shall support direct integration with satellite communication devices (VSAT terminals, LEO satellite networks) for remote or offline coverage.

### CONSTRAINT-FR9.2-offline-queue
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.3.9
- type: protocol
- content: The system shall maintain an offline queue of messages/alerts, automatically sending them once satellite or terrestrial connectivity is restored.

### CONSTRAINT-FR10.1-scheduled-education
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.4.10
- type: protocol
- content: The system shall support scheduled push of educational messages (e.g., monthly test alerts, preparedness tips).

### CONSTRAINT-FR10.2-localized-outreach
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.4.10
- type: protocol
- content: The system shall allow targeted community or district outreach via localized channels.

### CONSTRAINT-FR11.1-recovery-info
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.4.11
- type: protocol
- content: The system shall continue to disseminate recovery and rehabilitation information (e.g., location of shelters, missing persons announcements).

### CONSTRAINT-FR11.2-public-feedback
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.4.11
- type: protocol
- content: The system shall allow direct feedback or incident reporting from the public (hotlines, interactive SMS).

### CONSTRAINT-FR12.1-rbac-roles
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.5.12
- type: schema
- content: The system shall have a role-based access control module (e.g., super-admin, EOC operator, NGO coordinator, read-only).

### CONSTRAINT-FR12.2-audit-logs
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.5.12
- type: schema
- content: The system shall log all user actions for auditing purposes.

### CONSTRAINT-FR13.1-realtime-dashboards
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.5.13
- type: protocol
- content: The system shall generate real-time dashboards on active alerts, coverage metrics, and system status.

### CONSTRAINT-FR13.2-after-action
- source: Requirements Document for Unified Emergency Communication Platform.pdf §4.5.13
- type: schema
- content: The system shall provide after-action reports for each incident, with timeline, number of alerts sent, recipients reached, etc.

---

## Non-Functional Requirements (NFR1 – NFR15)

### CONSTRAINT-NFR1-broadcast-latency
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.1
- type: nfr
- content: The system shall broadcast high-priority alerts (e.g., national SMS) within 1 minute of approval under normal network conditions.

### CONSTRAINT-NFR2-concurrent-users
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.1
- type: nfr
- content: The system's portal shall support up to 1000 concurrent users (including first responders, EOC staff, and NGO reps) without degradation.

### CONSTRAINT-NFR3-availability
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.2
- type: nfr
- content: The system shall be available 99.9% of the time, with scheduled maintenance windows announced in advance.

### CONSTRAINT-NFR4-redundancy
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.2
- type: nfr
- content: The system shall have redundant servers (e.g., active-active or active-passive) and at least one backup power supply for critical nodes.

### CONSTRAINT-NFR5-scale-throughput
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.3
- type: nfr
- content: The system must scale to serve millions of SMS/cell broadcast alerts per minute if needed (e.g., for nationwide emergencies).

### CONSTRAINT-NFR6-extensibility
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.3
- type: nfr
- content: The architecture must allow easy addition of new technologies (e.g., new 5G expansions, next-gen satellite services).

### CONSTRAINT-NFR7-e2e-encryption
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.4
- type: nfr
- content: Implement end-to-end encryption for sensitive communications among first responders.

### CONSTRAINT-NFR8-data-protection
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.4
- type: nfr
- content: Follow data protection laws (local laws, GDPR-like standards) for storing or processing personal info.

### CONSTRAINT-NFR9-audit-trails
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.4
- type: schema
- content: Provide audit trails for every alert or message disseminated, along with identity of the approver.

### CONSTRAINT-NFR10-ui-usability
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.5
- type: nfr
- content: The user interface (UI) must be intuitive and require minimal training for new operators.

### CONSTRAINT-NFR11-accessibility
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.5
- type: nfr
- content: All public-facing alerts and official messages shall support local languages, sign-language overlays (for TV), and screen-reader compatibility.

### CONSTRAINT-NFR12-modular-design
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.6
- type: nfr
- content: The system shall follow modular design and established coding standards for easier upgrades.

### CONSTRAINT-NFR13-documentation
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.6
- type: nfr
- content: System documentation (admin guides, user manuals, SOPs) must be regularly updated.

### CONSTRAINT-NFR14-cap-protocol
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.7
- type: api-contract
- content: The system shall implement CAP (Common Alerting Protocol) for consistent alert formatting.

### CONSTRAINT-NFR15-open-apis
- source: Requirements Document for Unified Emergency Communication Platform.pdf §5.7
- type: api-contract
- content: Provide well-documented APIs for integration with external or legacy systems.

---

## Operational & Environmental Constraints

### CONSTRAINT-op-scenarios
- source: Requirements Document for Unified Emergency Communication Platform.pdf §6.1 (Operational Scenarios)
- type: protocol
- content: System must support three scenario classes — (1) Major Disasters (earthquakes, floods, storms) with very high alert volume in short time and possible partial infrastructure collapse; (2) Localized Incidents (fires, radiological, chemical) with targeted geo-based alerts; (3) Planned Drills with simulated alerts requiring test-mode or disclaimers and minimal disruption to public channels.

### CONSTRAINT-op-environment
- source: Requirements Document for Unified Emergency Communication Platform.pdf §6.2 (Environmental Constraints)
- type: nfr
- content: System must function in varying environments — from city centers with 4G/5G to remote rural areas reliant on HF radio or solar power. Must handle extreme weather conditions (power outages, flooding at telecom facilities).

---

## Data Schema Constraints

### CONSTRAINT-data-alert-metadata
- source: Requirements Document for Unified Emergency Communication Platform.pdf §7.1 (Metadata for Alerts)
- type: schema
- content: Alerts must carry: incident type, severity, location (GPS coordinates), recommended protective actions, timestamps, triggers, approval logs.

### CONSTRAINT-data-user-roles
- source: Requirements Document for Unified Emergency Communication Platform.pdf §7.2 (User & Role Data)
- type: schema
- content: Maintain user profiles, permissions, contact details. Sensitive info (phone numbers, email IDs) must be protected.

### CONSTRAINT-data-sensor
- source: Requirements Document for Unified Emergency Communication Platform.pdf §7.3 (Sensor/IoT Data)
- type: schema
- content: Automated input from weather stations, seismic monitors, river gauges, etc. Data must be time-stamped and validated to prevent false positives.

---

## Assumptions & Dependencies

### CONSTRAINT-assumption-telecom-upgrade
- source: Requirements Document for Unified Emergency Communication Platform.pdf §8 (Assumptions & Dependencies, item i)
- type: protocol
- content: ASSUMPTION — Telecom operators commit to network upgrades (e.g., cell broadcast enablement, 5G expansions) that support large-scale emergency alerts.

### CONSTRAINT-assumption-legal-frameworks
- source: Requirements Document for Unified Emergency Communication Platform.pdf §8 (Assumptions & Dependencies, item ii)
- type: protocol
- content: ASSUMPTION — Government agencies (NADMO, MoCD) will enact legal frameworks that allow cross-agency data exchange and emergency overrides.

### CONSTRAINT-dependency-funding
- source: Requirements Document for Unified Emergency Communication Platform.pdf §8 (Assumptions & Dependencies, item iii)
- type: protocol
- content: DEPENDENCY — Regular budget allocation or PPPs to maintain the system.

### CONSTRAINT-dependency-public-education
- source: Requirements Document for Unified Emergency Communication Platform.pdf §8 (Assumptions & Dependencies, item iv)
- type: protocol
- content: DEPENDENCY — End-users (public, community leaders) are continuously educated on how to respond to system alerts.

---

## Acceptance Criteria (System-Level)

### CONSTRAINT-accept-interop-test
- source: Requirements Document for Unified Emergency Communication Platform.pdf §9 (Key Acceptance Criteria, item i)
- type: nfr
- content: Interoperability Test — successful multi-channel alert tests (SMS, cell broadcast, radio/TV interruption, satellite) within established performance thresholds.

### CONSTRAINT-accept-security-audit
- source: Requirements Document for Unified Emergency Communication Platform.pdf §9 (Key Acceptance Criteria, item ii)
- type: nfr
- content: Security Audit — no critical vulnerabilities found during penetration testing.

### CONSTRAINT-accept-coverage
- source: Requirements Document for Unified Emergency Communication Platform.pdf §9 (Key Acceptance Criteria, item iii)
- type: nfr
- content: Coverage & Reliability — high satisfaction from pilot test sites, including remote communities relying on HF or satellite links.

### CONSTRAINT-accept-scale
- source: Requirements Document for Unified Emergency Communication Platform.pdf §9 (Key Acceptance Criteria, item iv)
- type: nfr
- content: Scalability — must prove stable operation during a simulated nationwide alert scenario (peak load stress test).

### CONSTRAINT-accept-public-drill
- source: Requirements Document for Unified Emergency Communication Platform.pdf §9 (Key Acceptance Criteria, item v)
- type: nfr
- content: Public Outreach — system must be used in at least one successful public drill with recognized user clarity and minimal confusion.
