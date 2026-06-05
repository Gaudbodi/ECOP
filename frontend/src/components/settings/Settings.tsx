import type { User } from '../../api/types'
import { WebhookConfig } from './WebhookConfig'
import { TestDispatcher } from './TestDispatcher'
import { ProviderStatus } from './ProviderStatus'

/**
 * Settings — top-level Settings tab. Composes three sections:
 *   1. WebhookConfig (read-only per A5/A7)
 *   2. TestDispatcher (Admin-only; renders explanatory placeholder otherwise)
 *   3. ProviderStatus (read-only port of the legacy "CONFIGURED" cards)
 *
 * Pass-through `user` rather than calling `useApi('/api/v1/me')` here
 * because App.tsx already fetches it once for Navbar — passing it down
 * avoids a duplicate request.
 */

interface SettingsProps {
  user: User | null
}

export function Settings({ user }: SettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-mono uppercase tracking-[0.22em] text-sky-300/80 mb-1">
          Operations
        </p>
        <h2 className="text-3xl sm:text-4xl font-bold leading-tight">Settings</h2>
        <p className="text-sm text-white/60 mt-1 max-w-2xl">
          Webhook contracts, test dispatch, and provider status. Sensitive
          values stay server-side; this surface is read-only by design.
        </p>
      </div>
      <WebhookConfig />
      <TestDispatcher userRole={user?.role} />
      <ProviderStatus />
    </div>
  )
}
