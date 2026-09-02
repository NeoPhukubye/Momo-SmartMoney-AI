import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, AlertTriangle, PiggyBank, MessageCircle, Shield, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import api from '../services/api'

export default function Dashboard() {
  const { t } = useTranslation()
  const { announce } = useAccessibility()
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

  if (loading) {
    return (
      <div className="space-y-4" role="status" aria-label={t('common.loading')}>
        <div className="h-8 bg-gray-200 rounded animate-pulse w-1/3" aria-hidden="true" />
        <div className="grid grid-cols-2 gap-3">
          <div className="h-24 bg-gray-200 rounded-xl animate-pulse" aria-hidden="true" />
          <div className="h-24 bg-gray-200 rounded-xl animate-pulse" aria-hidden="true" />
        </div>
        <div className="h-28 bg-gray-200 rounded-xl animate-pulse" aria-hidden="true" />
        <span className="sr-only">{t('common.loading')}</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-mtn-dark">{t('common.dashboard')}</h2>

      {/* Balance Cards */}
      <div className="grid grid-cols-2 gap-3" role="region" aria-label={t('dashboard.spending_summary')}>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-4 h-4 text-green-500" aria-hidden="true" />
            <span className="text-xs text-gray-500">{t('dashboard.income')}</span>
          </div>
          <p className="text-lg font-bold text-green-600" aria-label={`${t('dashboard.income')}: R${(summary?.total_income || 0).toLocaleString()}`}>
            R{(summary?.total_income || 0).toLocaleString()}
          </p>
          <p className="text-xs text-gray-400 mt-1">{t('dashboard.last_30_days')}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 mb-1">
            <TrendingDown className="w-4 h-4 text-red-500" aria-hidden="true" />
            <span className="text-xs text-gray-500">{t('dashboard.spent')}</span>
          </div>
          <p className="text-lg font-bold text-red-500" aria-label={`${t('dashboard.spent')}: R${(summary?.total_expenses || 0).toLocaleString()}`}>
            R{(summary?.total_expenses || 0).toLocaleString()}
          </p>
          <p className="text-xs text-gray-400 mt-1">{t('dashboard.last_30_days')}</p>
        </div>
      </div>

      {/* Net Balance */}
      <div className="gradient-card rounded-xl p-4 shadow-sm" role="region" aria-label={t('dashboard.net_balance')}>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <PiggyBank className="w-5 h-5 text-mtn-blue" aria-hidden="true" />
              <span className="text-sm text-mtn-blue font-medium">{t('dashboard.net_balance')}</span>
            </div>
            <p className="text-2xl font-bold text-mtn-blue" aria-label={`${t('dashboard.net_balance')}: R${(summary?.net || 0).toLocaleString()}`}>
              R{(summary?.net || 0).toLocaleString()}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-mtn-blue/70">
              {(summary?.net || 0) >= 0 ? t('dashboard.on_track') : t('dashboard.watch_spending')}
            </p>
          </div>
        </div>
      </div>

      {/* Scam Alerts */}
      {flagged.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4" role="alert" aria-label={t('dashboard.scam_alerts')}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" aria-hidden="true" />
              <span className="font-semibold text-red-700">{t('dashboard.scam_alerts')} ({flagged.length})</span>
            </div>
            <Shield className="w-5 h-5 text-red-400" aria-hidden="true" />
          </div>
          {flagged.slice(0, 2).map((txn) => (
            <div key={txn.id} className="text-sm text-red-600 mt-2 pl-7">
              <span className="font-medium">R{txn.amount}</span> to {txn.counterparty_name || txn.counterparty_phone}
              <p className="text-xs text-red-400 mt-0.5">{txn.risk_reason}</p>
            </div>
          ))}
          <button
            onClick={() => navigate('/transactions')}
            className="mt-3 text-xs text-red-600 font-medium flex items-center gap-1 pl-7"
            aria-label={t('dashboard.view_all_flagged')}
          >
            {t('dashboard.view_all_flagged')} <ChevronRight className="w-3 h-3" aria-hidden="true" />
          </button>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3" role="region" aria-label={t('dashboard.quick_actions')}>
        <button
          onClick={() => navigate('/chat')}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 text-left hover:border-mtn-yellow transition focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
          aria-label={`${t('dashboard.ask_coach')}: ${t('dashboard.get_advice')}`}
        >
          <MessageCircle className="w-6 h-6 text-mtn-blue mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-gray-800">{t('dashboard.ask_coach')}</p>
          <p className="text-xs text-gray-400">{t('dashboard.get_advice')}</p>
        </button>
        <button
          onClick={() => navigate('/stokvel')}
          className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 text-left hover:border-mtn-yellow transition focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
          aria-label={`${t('dashboard.my_stokvel')}: ${t('dashboard.group_savings')}`}
        >
          <PiggyBank className="w-6 h-6 text-mtn-blue mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-gray-800">{t('dashboard.my_stokvel')}</p>
          <p className="text-xs text-gray-400">{t('dashboard.group_savings')}</p>
        </button>
      </div>

      {/* Spending Categories */}
      {summary?.by_category && Object.keys(summary.by_category).length > 0 && (
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100" role="region" aria-label={t('dashboard.where_money_goes')}>
          <h3 className="font-semibold text-sm text-gray-700 mb-3">{t('dashboard.where_money_goes')}</h3>
          {Object.entries(summary.by_category)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 6)
            .map(([category, amount]) => {
              const total = summary.total_expenses || 1
              const pct = ((amount / total) * 100).toFixed(0)
              return (
                <div key={category} className="mb-2">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm capitalize text-gray-600">{category.replace('_', ' ')}</span>
                    <span className="text-sm font-medium">R{amount.toLocaleString()} ({pct}%)</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2" role="progressbar" aria-valuenow={pct} aria-valuemin="0" aria-valuemax="100" aria-label={`${category}: ${pct}%`}>
                    <div
                      className="bg-mtn-blue h-2 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
        </div>
      )}

      {/* Daily Tip */}
      {tips.length > 0 && (
        <div className="bg-blue-50 rounded-xl p-4 border border-blue-100" role="complementary" aria-label={t('dashboard.ai_tip')}>
          <h3 className="text-sm font-semibold text-mtn-blue mb-1">{t('dashboard.ai_tip')}</h3>
          <p className="text-sm text-gray-700">{tips[Math.floor(Math.random() * tips.length)]}</p>
        </div>
      )}
    </div>
  )
}
