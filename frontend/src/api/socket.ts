import { io, type Socket } from 'socket.io-client'
import type { CapAlert } from './types'

// Server -> client events emitted on the default Socket.IO namespace.
// Source of truth: ghana_cap_app.py:283 (process_alert_logic emit `new_alert`)
// and :422 (validate_alert emit `alert_updated`).
export interface ServerToClientEvents {
  new_alert: (alert: CapAlert) => void
  alert_updated: (alert: CapAlert) => void
}

// Client -> server events. Reserved for future agent-streaming etc.;
// empty in Phase 4. Keeps the typed Socket generic intact for callers.
// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface ClientToServerEvents {}

// Singleton — one connection across the whole app. Plan 03's useAlerts hook
// + future hooks subscribe via .on()/.off() with their own cleanup.
//
// In dev, Vite proxies /socket.io with ws:true (vite.config.ts). In prod,
// io() with no URL connects to current origin (where Flask serves both the
// SPA and Socket.IO). RESEARCH.md Pattern 5: module-scope construction is
// safe under React StrictMode because the socket isn't created inside an
// effect; subscribers must use cleanup functions.
export const socket: Socket<ServerToClientEvents, ClientToServerEvents> = io({
  autoConnect: true,
  transports: ['websocket', 'polling'],
})
