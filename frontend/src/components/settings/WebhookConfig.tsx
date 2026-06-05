import { useEffect, useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'

/**
 * WebhookConfig — read-only display per phase planning A5/A7.
 *
 * Replaces the legacy server-side script-write of the webhook URL
 * (`<script>...origin + '/api/v1/alerts/gmet/webhook'</script>` in
 * ghana_cap_dashboard.html:511) with a JSX template literal. The
 * `origin` is read from `window.location.origin` inside a useEffect
 * to stay SSR-safe (window is undefined during build / SSG).
 *
 * Why read-only: A5 explicitly defers generate/revoke key controls to
 * a follow-up phase. Multi-key rotation requires a backend key store;
 * v1 keeps the operator-visible surface minimal so we don't ship UI
 * for unimplemented backend.
 *
 * Key value never reaches the browser — only a masked placeholder
 * (mitigates T-04-26 information disclosure).
 */
export function WebhookConfig() {
  const [origin, setOrigin] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    setOrigin(window.location.origin)
  }, [])

  const webhookUrl = origin ? `${origin}/api/v1/alerts/gmet/webhook` : ''

  async function copy() {
    if (!webhookUrl) return
    try {
      await navigator.clipboard.writeText(webhookUrl)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard API unavailable (e.g. insecure context) — operator
      // can still select-and-copy from the rendered <code> element.
    }
  }

  return (
    <GlassCard variant="card" className="space-y-3">
      <h3 className="text-lg font-bold">GMeT Ingress Webhook</h3>

      <div>
        <div className="text-xs uppercase tracking-wide text-white/50 mb-1">
          Endpoint URL
        </div>
        <div className="flex gap-2 items-stretch">
          <code className="flex-1 font-mono text-sm bg-black/40 border border-white/10 rounded-md px-3 py-2 truncate">
            {webhookUrl || 'Loading…'}
          </code>
          <button
            type="button"
            onClick={copy}
            disabled={!origin}
            className="px-3 py-2 rounded-md border border-white/15 bg-white/5 hover:bg-white/10 text-sm disabled:opacity-50 inline-flex items-center gap-1"
            title="Copy URL"
            aria-label="Copy webhook URL"
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            <span className="sr-only">Copy URL</span>
          </button>
        </div>
      </div>

      <div>
        <div className="text-xs uppercase tracking-wide text-white/50 mb-1">
          Required Header
        </div>
        <code className="block font-mono text-sm bg-black/40 border border-white/10 rounded-md px-3 py-2">
          X-CAP-API-KEY: ••••••••••••••••
        </code>
        <p className="mt-1 text-xs text-white/60">
          Key is configured server-side. To rotate, update the{' '}
          <code className="font-mono">GMET_WEBHOOK_API_KEY</code> environment
          variable and restart the service.
        </p>
      </div>

      <div className="text-xs text-amber-300/80 border-t border-white/10 pt-3">
        Generate / revoke key controls are deferred to a follow-up phase.
        Multi-key rotation requires a backend key store; v1 of Webhook
        Config is read-only by design (per phase planning A5/A7).
      </div>
    </GlassCard>
  )
}
