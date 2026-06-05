import type { CapAlert, Role } from '../../api/types'
import { AudioPlayer } from './AudioPlayer'
import { DispatchStatus } from './DispatchStatus'
import { ValidatorControls } from './ValidatorControls'
import { LifecycleControls } from './LifecycleControls'

interface AlertDetailProps {
  alert: CapAlert
  userRole: Role | undefined
}

// Languages pinned to v1: English / Twi / Hausa (RESEARCH.md Pattern 8 +
// REQ-translation). Looping over Object.keys(translations) instead would
// render any future language without UI review.
const TRANSLATION_LANGS = ['English', 'Twi', 'Hausa'] as const

/**
 * AlertDetail — expanded grid.
 *
 * Ports ghana_cap_dashboard.html:416-435 (Sender / Description / Workflow
 * Status), plus translations + per-language audio + instruction (the
 * existing dashboard misses these — Phase 4 adds them per ROADMAP §90.7).
 *
 * The validated_by / rejected_by metadata is rendered inline — no separate
 * banner — matching the data already on the alert document.
 */
export function AlertDetail({ alert, userRole }: AlertDetailProps) {
  const translations = alert.translations ?? {}
  const audio = alert.audio_links ?? {}

  return (
    <div className="px-6 pb-6 bg-black/20 rounded-b-xl border-t border-white/10">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
        <div>
          <div className="text-xs uppercase tracking-wide text-white/50 mb-1">
            Sender Credentials
          </div>
          <div className="text-sm">{alert.sender_name}</div>
          <div className="text-xs text-white/60">ID: {alert.sender_id}</div>
          <div className="text-xs text-white/60">Agency: {alert.sender_agency}</div>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-white/50 mb-1">Description</div>
          <div className="text-sm whitespace-pre-wrap">{alert.description}</div>
          {alert.instruction && (
            <>
              <div className="text-xs uppercase tracking-wide text-white/50 mt-3 mb-1">
                Instruction
              </div>
              <div className="text-sm whitespace-pre-wrap">{alert.instruction}</div>
            </>
          )}
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-white/50 mb-1">
            Workflow Status
          </div>
          <DispatchStatus alert={alert} />
          {alert.validated_by && (
            <div className="text-xs text-white/60 mt-2">
              Validated by {alert.validated_by} at {alert.validated_at}
            </div>
          )}
          {alert.rejected_by && (
            <div className="text-xs text-red-300 mt-2">
              Rejected by {alert.rejected_by}: {alert.rejected_reason}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        {TRANSLATION_LANGS.map((lang) => (
          <div key={lang}>
            <div className="text-xs uppercase tracking-wide text-white/50 mb-1">{lang}</div>
            <div className="text-sm whitespace-pre-wrap mb-2 min-h-[2.5rem]">
              {translations[lang] || (
                <span className="text-white/40 italic">Not translated</span>
              )}
            </div>
            <AudioPlayer src={audio[lang]} language={lang} />
          </div>
        ))}
      </div>

      <ValidatorControls alert={alert} userRole={userRole} />
      <LifecycleControls alert={alert} userRole={userRole} />

      {alert.lifecycle_history && alert.lifecycle_history.length > 0 && (
        <div className="mt-5 pt-4 border-t border-white/10">
          <div className="text-xs uppercase tracking-wide text-white/50 mb-2">
            Lifecycle history
          </div>
          <ul className="space-y-1.5 text-xs">
            {alert.lifecycle_history.map((h, i) => (
              <li
                key={`${h.at}-${i}`}
                className="flex items-start gap-2 text-white/75"
              >
                <span
                  className={`mt-0.5 inline-block w-1.5 h-1.5 rounded-full shrink-0 ${
                    h.action === 'terminate' ? 'bg-emerald-400' : 'bg-rose-400'
                  }`}
                />
                <span className="font-mono text-white/55">{h.at}</span>
                <span className="font-semibold uppercase tracking-wide text-[10px]">
                  {h.action === 'terminate' ? 'TERMINATED' : 'EXTENDED'}
                </span>
                <span className="text-white/55">·</span>
                <span>{h.by}</span>
                {h.severity_after && h.severity_after !== h.severity_before && (
                  <span className="ml-1 px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-200 text-[10px] font-mono">
                    {h.severity_before} → {h.severity_after}
                  </span>
                )}
                <span className="text-white/55 italic">— {h.reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
