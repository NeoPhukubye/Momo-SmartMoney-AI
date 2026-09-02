import { useState, useEffect } from 'react'
import { Users, Plus, ArrowRight, PiggyBank, X, Phone, CheckCircle2, ShieldCheck } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import api from '../services/api'

export default function Stokvel() {
  const { t } = useTranslation()
  const { announce } = useAccessibility()
  const [stokvels, setStokvels] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', contribution_amount: '', frequency: 'monthly' })
  const [loading, setLoading] = useState(true)
  const [createError, setCreateError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadStokvels()
  }, [])

  const loadStokvels = async () => {
    try {
      const { data } = await api.get('/api/stokvels/')
      setStokvels(data)
      announce(t('a11y.loading_complete'))
    } catch (err) {
      announce(t('a11y.error_occurred'), 'assertive')
    } finally {
      setLoading(false)
    }
  }

  const createStokvel = async (e) => {
    e.preventDefault()
    setCreateError('')
    setSubmitting(true)
    try {
      await api.post('/api/stokvels/', {
        ...form,
        contribution_amount: parseFloat(form.contribution_amount),
      })
      setShowCreate(false)
      setForm({ name: '', contribution_amount: '', frequency: 'monthly' })
      loadStokvels()
      announce('Stokvel created successfully')
    } catch (err) {
      const detail = err.response?.data?.detail || t('common.error')
      setCreateError(detail)
      announce(t('a11y.error_occurred'), 'assertive')
    } finally {
      setSubmitting(false)
    }
  }

  const contribute = async (stokvelId) => {
    try {
      await api.post(`/api/stokvels/${stokvelId}/contribute`)
      loadStokvels()
      announce('Contribution recorded')
    } catch (err) {
      announce(t('a11y.error_occurred'), 'assertive')
    }
  }

  const totalMembers = stokvels.reduce((acc, s) => acc + (s.member_count || 0), 0)
  const totalMtnMembers = stokvels.reduce((acc, s) => acc + (s.mtn_member_count || 0), 0)
  const totalContrib = stokvels.reduce((acc, s) => acc + (s.contribution_amount || 0) * (s.member_count || 0), 0)

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl p-5 bg-gradient-to-br from-mtn-yellow to-mtn-yellow-deep text-mtn-blue-deep shadow-glow-yellow">
        <div className="absolute -top-16 -right-16 w-48 h-48 rounded-full bg-white/20 blur-3xl pointer-events-none" aria-hidden="true" />
        <div className="relative flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.18em] font-bold opacity-70">Stokvels</p>
            <h2 className="font-display text-3xl font-extrabold tracking-tight mt-0.5">{t('stokvel.title')}</h2>
            <p className="text-sm opacity-80 mt-1">Save together, grow together.</p>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-white/25 backdrop-blur flex items-center justify-center flex-shrink-0">
            <PiggyBank className="w-6 h-6" aria-hidden="true" />
          </div>
        </div>

<div className="relative grid grid-cols-3 gap-2 mt-5">
          <div className="rounded-2xl bg-white/20 backdrop-blur p-3">
            <p className="text-[10px] uppercase tracking-widest opacity-70 font-semibold">Groups</p>
            <p className="font-display font-bold text-xl mt-0.5">{stokvels.length}</p>
          </div>
          <div className="rounded-2xl bg-white/20 backdrop-blur p-3">
            <p className="text-[10px] uppercase tracking-widest opacity-70 font-semibold">Members</p>
            <p className="font-display font-bold text-xl mt-0.5">{totalMembers}</p>
          </div>
          <div className="rounded-2xl bg-white/20 backdrop-blur p-3">
            <p className="text-[10px] uppercase tracking-widest opacity-70 font-semibold">MTN</p>
            <p className="font-display font-bold text-xl mt-0.5">{totalMtnMembers}</p>
          </div>
        </div>
      </section>

      <div className="flex justify-between items-center">
        <h3 className="font-display font-bold text-mtn-dark">Your groups</h3>
        <button
          onClick={() => setShowCreate(true)}
          className="inline-flex items-center gap-1.5 bg-mtn-blue text-white text-sm font-semibold px-3.5 py-2 rounded-xl shadow-soft hover:bg-mtn-blue-light lift focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
          aria-label={t('stokvel.new')}
        >
          <Plus className="w-4 h-4" aria-hidden="true" />
          {t('stokvel.new')}
        </button>
      </div>

      {/* MTN requirement notice */}
      <div className="flex items-start gap-3 rounded-2xl border border-mtn-yellow/30 bg-gradient-to-br from-mtn-yellow/10 to-amber-50 p-3.5">
        <div className="w-9 h-9 rounded-xl bg-mtn-yellow/30 flex items-center justify-center flex-shrink-0" aria-hidden="true">
          <ShieldCheck className="w-4 h-4 text-mtn-blue-deep" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-mtn-blue-deep">MTN member required</p>
          <p className="text-xs text-slate-600 mt-0.5">
            Every MoMo Stokvel must have at least one member with an MTN number. All members share the same authority.
          </p>
        </div>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in" role="dialog" aria-modal="true">
          <form onSubmit={createStokvel} className="relative w-full max-w-md bg-white rounded-3xl p-6 shadow-lift animate-slide-up" aria-label={t('stokvel.create')}>
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="absolute top-4 right-4 w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 hover:bg-slate-100 focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
              aria-label="Close"
            >
              <X className="w-4 h-4" />
            </button>
            <div className="mb-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-mtn-yellow to-mtn-yellow-deep flex items-center justify-center mb-3">
                <PiggyBank className="w-6 h-6 text-mtn-blue-deep" aria-hidden="true" />
              </div>
              <h3 className="font-display text-xl font-bold text-mtn-dark">{t('stokvel.create')}</h3>
              <p className="text-sm text-slate-500">Set up a new savings group.</p>
            </div>

            <div className="mb-4 flex items-start gap-2 rounded-2xl border border-mtn-yellow/30 bg-mtn-yellow/10 p-3">
              <Phone className="w-4 h-4 text-mtn-blue-deep mt-0.5 flex-shrink-0" aria-hidden="true" />
              <p className="text-xs text-slate-700 leading-relaxed">
                Your registered phone number must be an <span className="font-semibold">MTN</span> number to create a MoMo Stokvel. All members will share equal authority.
              </p>
            </div>

            {createError && (
              <div className="mb-4 flex items-start gap-2 px-3 py-2.5 rounded-xl bg-red-50 border border-red-100" role="alert" aria-live="assertive">
                <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" aria-hidden="true" />
                <p className="text-sm text-red-700">{createError}</p>
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label htmlFor="stokvel-name" className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">{t('stokvel.name_label')}</label>
                <input
                  id="stokvel-name"
                  placeholder={t('stokvel.name_label')}
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:border-mtn-blue focus:ring-4 focus:ring-mtn-blue/10 outline-none transition"
                  required
                />
              </div>
              <div>
                <label htmlFor="stokvel-amount" className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">{t('stokvel.contribution_label')}</label>
                <input
                  id="stokvel-amount"
                  type="number"
                  placeholder={t('stokvel.contribution_label')}
                  value={form.contribution_amount}
                  onChange={(e) => setForm({ ...form, contribution_amount: e.target.value })}
                  className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:border-mtn-blue focus:ring-4 focus:ring-mtn-blue/10 outline-none transition"
                  required
                  inputMode="decimal"
                />
              </div>
              <div>
                <label htmlFor="stokvel-frequency" className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">{t('stokvel.frequency_label')}</label>
                <div className="grid grid-cols-3 gap-1.5">
                  {['weekly', 'biweekly', 'monthly'].map((f) => (
                    <button
                      key={f}
                      type="button"
                      onClick={() => setForm({ ...form, frequency: f })}
                      className={`px-3 py-2.5 rounded-2xl text-xs font-semibold transition border focus:outline-none focus-visible:ring-2 focus-visible:ring-mtn-yellow ${
                        form.frequency === f
                          ? 'bg-mtn-blue text-white border-mtn-blue shadow-soft'
                          : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {t(`stokvel.${f}`)}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 bg-gradient-to-r from-mtn-yellow to-mtn-yellow-deep text-mtn-blue-deep font-bold py-3 rounded-2xl shadow-glow-yellow hover:shadow-lift disabled:opacity-60 disabled:cursor-not-allowed focus-visible:ring-4 focus-visible:ring-mtn-blue/30 focus:outline-none transition"
              >
                {submitting ? t('auth.please_wait') : t('stokvel.create')}
              </button>
              <button type="button" onClick={() => setShowCreate(false)} className="flex-1 bg-slate-100 text-slate-700 font-semibold py-3 rounded-2xl hover:bg-slate-200 focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none transition">
                {t('common.cancel')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Stokvel List */}
      {loading ? (
        <div className="space-y-3" role="status" aria-label={t('common.loading')}>
          {[1, 2].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-slate-100 animate-pulse" aria-hidden="true" />
          ))}
          <span className="sr-only">{t('common.loading')}</span>
        </div>
      ) : stokvels.length === 0 ? (
        <div className="card-surface p-10 text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-mtn-yellow/30 to-mtn-yellow-deep/30 mx-auto flex items-center justify-center mb-3">
            <Users className="w-8 h-8 text-mtn-blue-deep" aria-hidden="true" />
          </div>
          <p className="font-display font-bold text-mtn-dark">{t('stokvel.no_stokvels')}</p>
          <p className="text-sm text-slate-500 mt-1">Tap the + button to start your first group.</p>
        </div>
      ) : (
        <div role="list" aria-label={t('stokvel.title')} className="space-y-3">
          {stokvels.map((s, idx) => {
            const gradients = [
              'from-mtn-blue to-mtn-blue-light',
              'from-violet-500 to-purple-600',
              'from-emerald-500 to-teal-600',
              'from-orange-500 to-rose-600',
            ]
            return (
              <div
                key={s.id}
                role="listitem"
                className="card-surface overflow-hidden lift animate-slide-up"
                style={{ animationDelay: `${idx * 60}ms` }}
                aria-label={`${s.name}: R${s.contribution_amount} per ${s.frequency}, ${s.member_count} ${t('stokvel.members')}`}
              >
                <div className={`h-2 bg-gradient-to-r ${gradients[idx % gradients.length]}`} aria-hidden="true" />
                <div className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="font-display font-bold text-mtn-dark truncate">{s.name}</h3>
                      <p className="text-sm text-slate-500 mt-0.5">
                        <span className="font-semibold text-mtn-blue">R{s.contribution_amount}</span> / {t(`stokvel.${s.frequency}`)}
                      </p>
                    </div>
                    <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full flex-shrink-0 ${
                      s.is_active
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                      {s.is_active ? t('stokvel.active') : t('stokvel.paused')}
                    </span>
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span className="inline-flex items-center gap-1.5">
                        <Users className="w-3.5 h-3.5" aria-hidden="true" />
                        <span className="font-medium">{s.member_count}</span>
                        <span>{t('stokvel.members')}</span>
                      </span>
                      {s.has_mtn_member ? (
                        <span
                          className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-mtn-yellow/20 text-mtn-blue-deep border border-mtn-yellow/40"
                          aria-label={`${s.mtn_member_count || 0} MTN members`}
                        >
                          <CheckCircle2 className="w-3 h-3" aria-hidden="true" />
                          {s.mtn_member_count || 0} MTN
                        </span>
                      ) : (
                        <span
                          className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200"
                          aria-label="No MTN member"
                        >
                          MTN needed
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => contribute(s.id)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-mtn-blue hover:text-mtn-blue-light focus-visible:underline focus:outline-none rounded px-2 py-1.5 hover:bg-mtn-blue/5 transition"
                      aria-label={`${t('stokvel.record_contribution')} - ${s.name}`}
                    >
                      {t('stokvel.record_contribution')}
                      <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}