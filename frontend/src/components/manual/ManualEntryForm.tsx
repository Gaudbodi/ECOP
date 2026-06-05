import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { motion } from 'motion/react'
import { resolveAlertArea, submitManualAlert } from '../../api/alerts'
import type { AreaResolveResponse } from '../../api/alerts'
import { ApiError } from '../../api/client'
import type { Severity, Urgency, ManualAlertRequest } from '../../api/types'
import type { MapTarget } from './MapPanel'
import { ConfirmationModal } from './ConfirmationModal'
import type { ConfirmationPayload } from './ConfirmationModal'

const SEVERITIES: Severity[] = ['Extreme', 'Severe', 'Moderate', 'Minor']
const URGENCIES: Urgency[] = ['Immediate', 'Expected', 'Future']

interface FormState {
  headline: string
  severity: Severity
  urgency: Urgency
  description: string
  instruction: string
  location: string
  radius: string  // string so the input can be empty / partially typed
}

const initialForm: FormState = {
  headline: '',
  severity: 'Severe',
  urgency: 'Immediate',
  description: '',
  instruction: '',
  location: '',
  radius: '',
}

interface ManualEntryFormProps {
  onTargetChange: (target: MapTarget | null) => void
  onSubmitted: () => void
}

export function ManualEntryForm({ onTargetChange, onSubmitted }: ManualEntryFormProps) {
  const [form, setForm] = useState<FormState>(initialForm)
  const [resolving, setResolving] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [resolution, setResolution] = useState<AreaResolveResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [confirmOpen, setConfirmOpen] = useState(false)

  function bind<K extends keyof FormState>(key: K) {
    return {
      value: form[key],
      onChange: (
        e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
      ) => setForm((f) => ({ ...f, [key]: e.target.value as FormState[K] })),
    }
  }

  async function resolveArea() {
    setError(null)
    if (!form.location.trim() && !form.description.trim()) {
      setError('Add a location (e.g. "Osu, Accra") or describe the area in the description before resolving.')
      return
    }
    setResolving(true)
    try {
      const radius = parseFloat(form.radius)
      const res = await resolveAlertArea({
        location: form.location.trim(),
        description: form.description.trim(),
        radius_km: Number.isFinite(radius) && radius > 0 ? radius : undefined,
      })
      setResolution(res)
      // If the agent picked the radius, surface the choice in the field so the
      // operator sees what was inferred and can override it.
      if (!form.radius || parseFloat(form.radius) <= 0) {
        setForm((f) => ({ ...f, radius: String(res.radius_km) }))
      }
      onTargetChange({
        lat: res.lat,
        lon: res.lon,
        radius_km: res.radius_km,
        label: res.label,
        event_type: res.event_type,
      })
    } catch (e) {
      const msg = e instanceof ApiError
        ? `${e.status}: ${(e.payload as { error?: string } | null)?.error ?? 'Could not resolve area'}`
        : String(e)
      setError(msg)
      setResolution(null)
      onTargetChange(null)
    } finally {
      setResolving(false)
    }
  }

  function buildConfirmation(): ConfirmationPayload | null {
    if (!resolution) return null
    const radius = parseFloat(form.radius)
    return {
      headline: form.headline,
      description: form.description,
      instruction: form.instruction,
      severity: form.severity,
      urgency: form.urgency,
      location: form.location || resolution.label,
      radius_km: Number.isFinite(radius) && radius > 0 ? radius : resolution.radius_km,
      target: {
        lat: resolution.lat,
        lon: resolution.lon,
        radius_km: Number.isFinite(radius) && radius > 0 ? radius : resolution.radius_km,
        label: resolution.label,
        event_type: resolution.event_type,
      },
    }
  }

  function handleReview(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!form.headline.trim() || !form.description.trim()) {
      setError('Add a headline and description before review.')
      return
    }
    if (!resolution) {
      setError('Resolve the affected area on the map before review.')
      return
    }
    setConfirmOpen(true)
  }

  async function handleConfirm() {
    if (!resolution) return
    setSubmitting(true)
    setError(null)
    try {
      const radius = parseFloat(form.radius)
      const payload: ManualAlertRequest = {
        headline: form.headline,
        severity: form.severity,
        urgency: form.urgency,
        description: form.description,
        instruction: form.instruction,
        latitude: resolution.lat,
        longitude: resolution.lon,
      } as unknown as ManualAlertRequest
      // Carry the radius + resolved label as additional metadata so the
      // server can persist the affected-area overlay if it grows that
      // capability later. Today the backend tolerates extras silently.
      ;(payload as unknown as Record<string, unknown>).affected_area_km = Number.isFinite(radius) && radius > 0 ? radius : resolution.radius_km
      ;(payload as unknown as Record<string, unknown>).affected_area_label = resolution.label
      const res = await submitManualAlert(payload)
      setSuccess(`Dispatched ${res.identifier}.`)
      setConfirmOpen(false)
      setForm(initialForm)
      setResolution(null)
      onTargetChange(null)
      onSubmitted()
    } catch (e) {
      const msg = e instanceof ApiError
        ? `${e.status}: ${(e.payload as { error?: string } | null)?.error ?? 'Submission failed'}`
        : String(e)
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  const confirmation = buildConfirmation()

  return (
    <>
      <form onSubmit={handleReview} className="space-y-4" noValidate>
        <Field id="headline" label="Headline">
          <input
            id="headline"
            type="text"
            required
            {...bind('headline')}
            placeholder="e.g. Heavy rain expected at Osu"
            className={inputClass}
          />
        </Field>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Field id="location" label="Location (place / district)">
            <input
              id="location"
              type="text"
              {...bind('location')}
              placeholder="Osu, Accra"
              className={inputClass}
            />
          </Field>
          <Field
            id="radius"
            label="Radius (km)"
            hint="Leave blank to let the agent infer"
          >
            <input
              id="radius"
              type="number"
              min="0"
              step="0.5"
              {...bind('radius')}
              placeholder="auto"
              className={inputClass}
            />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Field id="severity" label="Severity">
            <select id="severity" {...bind('severity')} className={inputClass}>
              {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </Field>
          <Field id="urgency" label="Urgency">
            <select id="urgency" {...bind('urgency')} className={inputClass}>
              {URGENCIES.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </Field>
        </div>

        <Field id="description" label="Description">
          <textarea
            id="description"
            rows={4}
            required
            {...bind('description')}
            placeholder="Describe the event clearly. Include location cues if you skip the location field — the agent reads this too."
            className={inputClass}
          />
        </Field>

        <Field id="instruction" label="Instructions for the public">
          <textarea
            id="instruction"
            rows={2}
            {...bind('instruction')}
            placeholder="What should the public do?"
            className={inputClass}
          />
        </Field>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={resolveArea}
            disabled={resolving}
            className="flex-1 min-w-[200px] px-4 py-3 rounded-xl border border-sky-400/40 bg-sky-500/10 text-sky-100 font-semibold hover:bg-sky-500/20 transition-colors disabled:opacity-50"
          >
            {resolving ? 'Resolving area…' : '✦ Resolve affected area'}
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="flex-1 min-w-[200px] px-4 py-3 rounded-xl bg-gradient-to-r from-sky-500 via-cyan-400 to-purple-500 text-slate-950 font-bold uppercase tracking-wide shadow-lg shadow-sky-500/30 disabled:opacity-50"
          >
            Review & dispatch →
          </button>
        </div>

        {resolution && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className={
              resolution.approximate
                ? 'rounded-xl border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs text-amber-100'
                : 'rounded-xl border border-emerald-400/25 bg-emerald-400/10 px-3 py-2 text-xs text-emerald-100'
            }
          >
            <div className="font-semibold">
              {resolution.approximate
                ? `Approximate area: ${resolution.label} — exact place not found, using ${resolution.region ? 'region' : 'national'} centre. Verify the pin & radius on the map.`
                : `Area resolved: ${resolution.label}`}
            </div>
            <div className={`font-mono mt-0.5 ${resolution.approximate ? 'text-amber-200/80' : 'text-emerald-200/80'}`}>
              {resolution.lat.toFixed(4)}, {resolution.lon.toFixed(4)} · {resolution.radius_km} km
              {' · '}radius source: {resolution.radius_source}
              {resolution.region ? ` · ${resolution.region}` : ''}
            </div>
          </motion.div>
        )}

        {error && (
          <div role="alert" className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-200">
            {error}
          </div>
        )}
        {success && (
          <div role="status" className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-sm text-emerald-200">
            {success}
          </div>
        )}
      </form>

      <ConfirmationModal
        open={confirmOpen}
        payload={confirmation}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleConfirm}
        submitting={submitting}
      />
    </>
  )
}

const inputClass =
  'w-full rounded-xl bg-slate-900/40 border border-white/15 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400/60 focus:border-sky-400/40 placeholder:text-white/40'

function Field({
  id,
  label,
  hint,
  children,
}: {
  id: string
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-[11px] font-mono uppercase tracking-[0.18em] text-white/60 mb-1.5">
        {label}
        {hint && <span className="ml-2 text-white/40 normal-case tracking-normal lowercase font-sans">— {hint}</span>}
      </label>
      {children}
    </div>
  )
}
