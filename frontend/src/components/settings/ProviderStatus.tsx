import { GlassCard } from '../ui/GlassCard'

/**
 * ProviderStatus — port of the SMS Provider + Enrichment Engine cards
 * from `ghana_cap_dashboard.html:515-526`.
 *
 * The static "CONFIGURED" badge is the v1 contract: it reflects whether
 * the credentials are present server-side, not whether the upstream API
 * is reachable. A future `/api/v1/system/health` endpoint can make the
 * badges reactive (probe-driven), but live polling is deferred — adding
 * a fake polling loop now would produce noise without any backend probe
 * to back it.
 *
 * Card descriptions are verbatim from the legacy template so no
 * operator-visible content drifts during the migration.
 */

interface ProviderStatusCard {
  title: string
  description: string
  status: 'CONFIGURED' | 'DEGRADED'
}

const PROVIDERS: ProviderStatusCard[] = [
  {
    title: 'SMS Provider',
    description:
      "Africa's Talking (primary), Twilio (fallback) — credentials configured server-side",
    status: 'CONFIGURED',
  },
  {
    title: 'Enrichment Engine',
    description:
      'OpenAI GPT-4o-mini (translation), OpenAI tts-1 / Khaya (TTS)',
    status: 'CONFIGURED',
  },
]

const BADGE_CLASS: Record<ProviderStatusCard['status'], string> = {
  CONFIGURED:
    'inline-block px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40',
  DEGRADED:
    'inline-block px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40',
}

export function ProviderStatus() {
  return (
    <GlassCard variant="card">
      <h3 className="text-lg font-bold mb-4">Provider Status</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PROVIDERS.map((p) => (
          <div
            key={p.title}
            className="rounded-lg border border-white/10 bg-black/20 p-4"
          >
            <div className="text-sm font-semibold mb-1">{p.title}</div>
            <p className="text-xs text-white/60 mb-3">{p.description}</p>
            <span className={BADGE_CLASS[p.status]}>{p.status}</span>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs text-white/50">
        Live health probes deferred to a follow-up phase; today's badge
        reflects whether the credential is set, not whether the upstream
        API is reachable.
      </p>
    </GlassCard>
  )
}
