import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, AlertTriangle, PiggyBank, MessageCircle, Shield, ChevronRight, Sparkles, ArrowUpRight, Wallet } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import api from '../services/api'

export default function Dashboard() {
  const { t } = useTranslation()
  const { announce, settings } = useAccessibility()
  const [summary, setSummary] = useState(null)
  const [tips, setTips] = useState([])
  const [flagged, setFlagged] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const [summaryRes, tipsRes, flaggedRes] = await Promise.allSettled([
        api.get('/api/transactions/summary'),
        api.get('/api/coaching/tips'),
        api.get('/api/transactions/flagged'),
      ])
      if (summaryRes.status === 'fulfilled') setSummary(summaryRes.value.data)
      if (tipsRes.status === 'fulfilled') setTips(tipsRes.value.data.tips || [])
      if (flaggedRes.status === 'fulfilled') setFlagged(flaggedRes.value.data || [])
      announce(t('a11y.loading_complete'))
    } catch (err) {
      announce(t('a11y.error_occurred'), 'assertive')
    } finally {
      setLoading(false)
    }
  }

  const net = summary?.net || 0
  const income = summary?.total_income || 0
  const expenses = summary?.total_expenses || 0
  const tip = tips[Math.floor(Math.random() * Math.max(tips.length, 1))]

  if (loading) {
    return (
      <div className="space-y-4" role="status" aria-label={t('common.loading')}>
        <div className="h-40 rounded-3xl bg-gradient-to-br from-slate-200 to-slate-100 animate-pulse" aria-hidden="true" />
        <div className="grid grid-cols-2 gap-3">
          <div className="h-24 rounded-2xl bg-slate-100 animate-pulse" aria-hidden="true" />
          <div className="h-24 rounded-2xl bg-slate-100 animate-pulse" aria-hidden="true" />
        </div>
        <div className="h-32 rounded-2xl bg-slate-100 animate-pulse" aria-hidden="true" />
        <span className="sr-only">{t('common.loading')}</span>
      </div>
    )
  }

  return (
    <div className="space-y-5 pb-2 animate-fade-in">
      {/* Hero Balance Card */}
      <section
        className="relative overflow-hidden rounded-3xl p-5 sm:p-6 text-white shadow-lift bg-night-sheen"
        aria-label={t('dashboard.net_balance')}
      >
        <div className="absolute -top-16 -right-12 w-56 h-56 rounded-full bg-mtn-yellow/25 blur-3xl pointer-events-none" aria-hidden="true" />
        <div className="absolute -bottom-20 -left-12 w-56 h-56 rounded-full bg-mtn-blue-light/30 blur-3xl pointer-events-none" aria-hidden="true" />

        <div className="relative">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-white/15 backdrop-blur flex items-center justify-center" aria-hidden="true">
                <Wallet className="w-4 h-4 text-mtn-yellow" />
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.18em] text-white/60 font-semibold">{t('dashboard.net_balance')}</p>
                <p className="text-xs text-white/70">{t('dashboard.last_30_days')}</p>
              </div>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-[11px] font-semibold backdrop-blur ${net >= 0 ? 'bg-emerald-400/20 text-emerald-100' : 'bg-red-400/20 text-red-100'}`}>
              {net >= 0 ? t('dashboard.on_track') : t('dashboard.watch_spending')}
            </span>
          </div>

          <p className="font-display text-4xl sm:text-5xl font-extrabold tracking-tight" aria-label={`${t('dashboard.net_balance')}: R${net.toLocaleString()}`}>
            R{net.toLocaleString()}
          </p>

          <div className="mt-5 grid grid-cols-2 gap-2.5">
            <MiniStat icon={TrendingUp} label={t('dashboard.income')} value={`R${income.toLocaleString()}`} tone="positive" />
            <MiniStat icon={TrendingDown} label={t('dashboard.spent')} value={`R${expenses.toLocaleString()}`} tone="negative" />
          </div>
        </div>
      </section>

      {/* Scam Alerts */}
      {flagged.length > 0 && (
        <section className="relative overflow-hidden rounded-2xl border border-red-100 bg-gradient-to-br from-red-50 to-rose-50 p-4 animate-slide-up" role="alert" aria-label={t('dashboard.scam_alerts')}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-red-100 text-red-600 flex items-center justify-center" aria-hidden="true">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div>
                <p className="font-display font-bold text-red-700">{t('dashboard.scam_alerts')}</p>
                <p className="text-[11px] text-red-500">{flagged.length} flagged</p>
              </div>
            </div>
            <Shield className="w-5 h-5 text-red-400" aria-hidden="true" />
          </div>
          {flagged.slice(0, 2).map((txn) => (
            <div key={txn.id} className="mt-2 pl-2 border-l-2 border-red-200">
              <p className="text-sm font-semibold text-red-700">
                R{txn.amount} <span className="font-normal text-red-500">to {txn.counterparty_name || txn.counterparty_phone}</span>
              </p>
              {txn.risk_reason && <p className="text-xs text-red-500 mt-0.5">{txn.risk_reason}</p>}
            </div>
          ))}
          <button
            onClick={() => navigate('/transactions')}
            className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-red-600 hover:text-red-700 focus-visible:underline focus:outline-none rounded px-1"
            aria-label={t('dashboard.view_all_flagged')}
          >
            {t('dashboard.view_all_flagged')}
            <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </section>
      )}

      {/* Quick Actions */}
      <section aria-label={t('dashboard.quick_actions')}>
        <h3 className="font-display text-sm font-bold text-slate-500 uppercase tracking-widest mb-2.5 px-1">
          {t('dashboard.quick_actions')}
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <QuickAction
            icon={MessageCircle}
            label={t('dashboard.ask_coach')}
            hint={t('dashboard.get_advice')}
            gradient="from-mtn-blue to-mtn-blue-light"
            onClick={() => navigate('/chat')}
            label_aria={t('dashboard.ask_coach')}
          />
          <QuickAction
            icon={PiggyBank}
            label={t('dashboard.my_stokvel')}
            hint={t('dashboard.group_savings')}
            gradient="from-mtn-yellow to-mtn-yellow-deep"
            iconClass="text-mtn-blue-deep"
            onClick={() => navigate('/stokvel')}
            label_aria={t('dashboard.my_stokvel')}
          />
        </div>
      </section>

      {/* Spending Categories */}
      {summary?.by_category && Object.keys(summary.by_category).length > 0 && (
        <section className="card-surface p-5" aria-label={t('dashboard.where_money_goes')}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-bold text-mtn-dark">{t('dashboard.where_money_goes')}</h3>
            <span className="text-[11px] text-slate-500">{Object.keys(summary.by_category).length} categories</span>
          </div>
          {Object.entries(summary.by_category)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 6)
            .map(([category, amount], idx) => {
              const total = summary.total_expenses || 1
              const pct = ((amount / total) * 100).toFixed(0)
              const colors = ['from-mtn-yellow to-mtn-yellow-deep', 'from-mtn-blue to-mtn-blue-light', 'from-emerald-400 to-emerald-600', 'from-violet-400 to-violet-600', 'from-orange-400 to-orange-600', 'from-rose-400 to-rose-600']
              return (
                <div key={category} className="mb-3 last:mb-0">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-sm font-medium capitalize text-slate-700">{category.replace('_', ' ')}</span>
                    <span className="text-sm font-semibold text-slate-900">
                      R{amount.toLocaleString()} <span className="text-slate-400 font-normal">· {pct}%</span>
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden" role="progressbar" aria-valuenow={pct} aria-valuemin="0" aria-valuemax="100" aria-label={`${category}: ${pct}%`}>
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${colors[idx % colors.length]} transition-all duration-700`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
        </section>
      )}

      {/* AI Tip */}
      {tip && (
        <section
          className="relative overflow-hidden rounded-2xl p-5 bg-gradient-to-br from-mtn-blue to-mtn-blue-deep text-white shadow-glow-blue animate-slide-up"
          role="complementary"
          aria-label={t('dashboard.ai_tip')}
        >
          <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-mtn-yellow/15 blur-2xl pointer-events-none" aria-hidden="true" />
          <div className="relative flex gap-3">
            <div className="w-10 h-10 rounded-xl bg-mtn-yellow/20 backdrop-blur flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-mtn-yellow" aria-hidden="true" />
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-[0.18em] text-mtn-yellow font-bold mb-1">{t('dashboard.ai_tip')}</p>
              <p className="text-sm leading-relaxed text-white/90">{tip}</p>
            </div>
          </div>
        </section>
      )}

      {/* Footer link */}
      <div className="text-center pt-2">
        <button
          onClick={() => navigate('/transactions')}
          className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-mtn-blue font-medium focus-visible:underline focus:outline-none rounded px-2 py-1"
        >
          {t('common.transactions')}
          <ArrowUpRight className="w-3 h-3" aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}

function MiniStat({ icon: Icon, label, value, tone }) {
  const toneClass = tone === 'positive' ? 'text-emerald-300' : 'text-rose-300'
  return (
    <div className="rounded-2xl bg-white/10 backdrop-blur border border-white/10 p-3">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className={`w-3.5 h-3.5 ${toneClass}`} aria-hidden="true" />
        <span className="text-[10px] uppercase tracking-widest text-white/60 font-semibold">{label}</span>
      </div>
      <p className="font-display font-bold text-base sm:text-lg">{value}</p>
    </div>
  )
}

function QuickAction({ icon: Icon, label, hint, gradient, onClick, label_aria, iconClass = 'text-white' }) {
  return (
    <button
      onClick={onClick}
      className={`group relative overflow-hidden rounded-2xl p-4 text-left text-white shadow-soft lift focus-visible:ring-4 focus-visible:ring-mtn-yellow/40 focus:outline-none bg-gradient-to-br ${gradient}`}
      aria-label={`${label}: ${hint}`}
    >
      <div className="absolute -top-10 -right-10 w-28 h-28 rounded-full bg-white/15 blur-2xl pointer-events-none transition-opacity opacity-60 group-hover:opacity-100" aria-hidden="true" />
      <div className="relative">
        <div className="w-11 h-11 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center mb-3">
          <Icon className={`w-5 h-5 ${iconClass}`} aria-hidden="true" />
        </div>
        <p className="font-display font-bold text-sm leading-tight">{label}</p>
        <p className="text-[11px] text-white/75 mt-0.5">{hint}</p>
      </div>
    </button>
  )
}