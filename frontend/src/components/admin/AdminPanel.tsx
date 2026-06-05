import { useEffect, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { motion } from 'motion/react'
import { Shield, UserPlus, Users } from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { ApiError } from '../../api/client'
import {
  createAdminUser,
  fetchAdminUsers,
  fetchStakeholders,
} from '../../api/admin'
import type { NewUserPayload, Stakeholder, User } from '../../api/types'

const ROLES: NewUserPayload['role'][] = ['cap generator', 'cap validator', 'Admin']

export function AdminPanel({ currentUser }: { currentUser: User | null }) {
  const [users, setUsers] = useState<User[]>([])
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [form, setForm] = useState<NewUserPayload>({
    email: '',
    name: '',
    agency: 'NADMO',
    role: 'cap generator',
    phone_number: '',
  })

  async function refresh() {
    setError(null)
    try {
      const [u, s] = await Promise.all([fetchAdminUsers(), fetchStakeholders()])
      setUsers(u.users)
      setStakeholders(s.stakeholders)
    } catch (e) {
      setError(
        e instanceof ApiError
          ? `${e.status}: ${(e.payload as { error?: string } | null)?.error ?? 'Failed to load admin data'}`
          : String(e),
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  function bind<K extends keyof NewUserPayload>(key: K) {
    return {
      value: (form[key] ?? '') as string,
      onChange: (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
        setForm((f) => ({ ...f, [key]: e.target.value as NewUserPayload[K] })),
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setCreating(true)
    setError(null)
    setSuccess(null)
    try {
      const payload: NewUserPayload = { ...form }
      if (!payload.phone_number) delete payload.phone_number
      const res = await createAdminUser(payload)
      setSuccess(`Onboarded ${res.user.name} (${res.user.role}, ${res.user.agency}).`)
      setForm({
        email: '',
        name: '',
        agency: form.agency,
        role: 'cap generator',
        phone_number: '',
      })
      await refresh()
    } catch (e) {
      setError(
        e instanceof ApiError
          ? `${e.status}: ${(e.payload as { error?: string } | null)?.error ?? 'Failed to create user'}`
          : String(e),
      )
    } finally {
      setCreating(false)
    }
  }

  const stakeholderById = new Map(stakeholders.map((s) => [s.id, s]))

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-mono uppercase tracking-[0.22em] text-sky-300/80 mb-1 flex items-center gap-2">
          <Shield className="h-3.5 w-3.5" /> Restricted · Super Admin only
        </p>
        <h2 className="text-3xl sm:text-4xl font-bold leading-tight">User onboarding</h2>
        <p className="text-sm text-white/60 mt-1 max-w-2xl">
          Bring new operators online from across Ghana's emergency-services
          stack. Pick a stakeholder, assign a role, and the platform handles
          the rest. Acting as <span className="font-mono text-sky-200">{currentUser?.email}</span>.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        <GlassCard className="xl:col-span-2 p-5 sm:p-6 space-y-4">
          <div className="flex items-center gap-2">
            <UserPlus className="h-4 w-4 text-sky-300" />
            <h3 className="text-lg font-semibold">Onboard a new operator</h3>
          </div>
          <form onSubmit={onSubmit} className="space-y-3" noValidate>
            <Field id="new-name" label="Full name">
              <input
                id="new-name"
                type="text"
                required
                {...bind('name')}
                placeholder="e.g. Ama Boateng"
                className={inputClass}
              />
            </Field>
            <Field id="new-email" label="Work email">
              <input
                id="new-email"
                type="email"
                required
                {...bind('email')}
                placeholder="ama.boateng@gfrs.gov.gh"
                className={inputClass}
              />
            </Field>
            <Field id="new-agency" label="Stakeholder agency">
              <select id="new-agency" required {...bind('agency')} className={inputClass}>
                {stakeholders.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.id} — {s.name}
                  </option>
                ))}
              </select>
              {form.agency && stakeholderById.has(form.agency) && (
                <p className="mt-1 text-[11px] text-white/50">
                  Scope: {stakeholderById.get(form.agency)?.scope}
                </p>
              )}
            </Field>
            <Field id="new-role" label="Role">
              <select id="new-role" required {...bind('role')} className={inputClass}>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-[11px] text-white/50">
                Super Admin is bootstrap-only and cannot be created from this panel.
              </p>
            </Field>
            <Field id="new-phone" label="Phone (optional, +233…)" hint="leave blank to receive OTP via email">
              <input
                id="new-phone"
                type="tel"
                {...bind('phone_number')}
                placeholder="+233 24 000 0000"
                className={inputClass}
              />
            </Field>
            <button
              type="submit"
              disabled={creating}
              className="w-full px-4 py-3 rounded-xl bg-gradient-to-r from-sky-500 via-cyan-400 to-purple-500 text-slate-950 font-bold uppercase tracking-wide shadow-lg shadow-sky-500/30 disabled:opacity-50"
            >
              {creating ? 'Onboarding…' : 'Onboard operator'}
            </button>
            {error && (
              <div role="alert" className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-200">
                {error}
              </div>
            )}
            {success && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                role="status"
                className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-sm text-emerald-200"
              >
                {success}
              </motion.div>
            )}
          </form>
        </GlassCard>

        <GlassCard className="xl:col-span-3 p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-sky-300" />
              <h3 className="text-lg font-semibold">Active operators</h3>
            </div>
            <span className="text-xs font-mono text-white/55">{users.length} record{users.length === 1 ? '' : 's'}</span>
          </div>

          {loading && (
            <div className="text-sm text-white/55 py-6 text-center">Loading…</div>
          )}
          {!loading && users.length === 0 && !error && (
            <div className="text-sm text-white/55 py-6 text-center">No operators yet.</div>
          )}

          {users.length > 0 && (
            <ul className="divide-y divide-white/5 -mx-2">
              {users.map((u) => {
                const stake = stakeholderById.get(u.agency)
                return (
                  <li key={u.staff_id} className="px-2 py-3 flex items-center gap-3">
                    <div
                      className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm shrink-0"
                      style={{
                        background: stake ? `${stake.color}1A` : 'rgba(255,255,255,0.06)',
                        border: `1px solid ${stake ? stake.color + '55' : 'rgba(255,255,255,0.12)'}`,
                        color: stake?.color ?? 'currentColor',
                      }}
                    >
                      {u.agency.slice(0, 2)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <div className="font-semibold truncate">{u.name}</div>
                        {u.is_superuser && (
                          <span className="px-1.5 py-0.5 rounded-md text-[9px] font-mono uppercase tracking-[0.18em] bg-amber-400/15 text-amber-200 border border-amber-400/30">
                            Super
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-white/55 truncate font-mono">
                        {u.email} · {u.staff_id}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-xs font-mono uppercase tracking-[0.16em] text-white/70">
                        {u.role}
                      </div>
                      <div className="text-[11px] text-white/45">{stake?.name ?? u.agency}</div>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </GlassCard>
      </div>
    </div>
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
