import { useState, useEffect } from 'react'
import { ArrowUpRight, ArrowDownLeft, AlertTriangle, ListFilter, Search } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import api from '../services/api'

export default function Transactions() {
  const { t } = useTranslation()
  const { announce } = useAccessibility()
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [query, setQuery] = useState('')

  useEffect(() => {
    loadTransactions()
  }, [])

  const loadTransactions = async () => {
    try {
      const { data } = await api.get('/api/transactions/')
      setTransactions(data)
      announce(t('a11y.loading_complete'))
    } catch (err) {
      announce(t('a11y.error_occurred'), 'assertive')
    } finally {
      setLoading(false)
    }
  }

  const filtered = transactions.filter(txn => {
    if (filter === 'income' && txn.direction !== 'in') return false
    if (filter === 'expenses' && txn.direction !== 'out') return false
    if (filter === 'flagged' && !txn.is_flagged) return false
    if (query) {
      const q = query.toLowerCase()
      return (
        (txn.counterparty_name || '').toLowerCase().includes(q) ||
        (txn.counterparty_phone || '').toLowerCase().includes(q) ||
        (txn.category || '').toLowerCase().includes(q)
      )
    }
    return true
  })

  const getRiskBadge = (level) => {
    const styles = {
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      high: 'bg-orange-100 text-orange-700 border-orange-200',
      critical: 'bg-red-100 text-red-700 border-red-200',
    }
    if (level === 'low' || !level) return null
    return (
      <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${styles[level]}`} role="status">
        <AlertTriangle className="w-2.5 h-2.5" aria-hidden="true" />
        {t(`transactions.risk_${level}`)}
      </span>
    )
  }

  const totals = {
    income: filtered.filter(x => x.direction === 'in').reduce((a, b) => a + b.amount, 0),
    expense: filtered.filter(x => x.direction === 'out').reduce((a, b) => a + b.amount, 0),
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-3xl font-extrabold text-mtn-dark tracking-tight">{t('transactions.title')}</h2>
          <p className="text-sm text-slate-500">{filtered.length} transactions</p>
        </div>
        <div className="hidden sm:flex w-12 h-12 rounded-2xl bg-gradient-to-br from-mtn-blue to-mtn-blue-deep items-center justify-center shadow-soft">
          <ListFilter className="w-5 h-5 text-mtn-yellow" aria-hidden="true" />
        </div>
      </div>

      {/* Summary strip */}
      {!loading && filtered.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl p-3 bg-gradient-to-br from-emerald-50 to-green-50 border border-emerald-100">
            <p className="text-[10px] uppercase tracking-widest text-emerald-700 font-bold">Income</p>
            <p className="font-display font-bold text-emerald-700 text-lg">R{totals.income.toLocaleString()}</p>
          </div>
          <div className="rounded-2xl p-3 bg-gradient-to-br from-rose-50 to-red-50 border border-rose-100">
            <p className="text-[10px] uppercase tracking-widest text-rose-700 font-bold">Expenses</p>
            <p className="font-display font-bold text-rose-700 text-lg">R{totals.expense.toLocaleString()}</p>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" aria-hidden="true" />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search transactions…"
          aria-label="Search transactions"
          className="w-full pl-11 pr-3 py-2.5 rounded-2xl bg-white border border-slate-200 text-sm focus:border-mtn-blue focus:ring-4 focus:ring-mtn-blue/10 outline-none transition"
        />
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1" role="tablist" aria-label={t('common.filter')}>
        {['all', 'income', 'expenses', 'flagged'].map((f) => (
          <button
            key={f}
            role="tab"
            aria-selected={filter === f}
            aria-controls="transactions-list"
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-full text-xs font-semibold whitespace-nowrap transition focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none ${
              filter === f
                ? 'bg-gradient-to-r from-mtn-yellow to-mtn-yellow-deep text-mtn-blue-deep shadow-soft'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {t(`transactions.filter_${f}`)}
          </button>
        ))}
      </div>

      {/* Transaction List */}
      <div id="transactions-list" role="tabpanel">
        {loading ? (
          <div className="space-y-2" role="status" aria-label={t('common.loading')}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 rounded-2xl bg-slate-100 animate-pulse" aria-hidden="true" />
            ))}
            <span className="sr-only">{t('common.loading')}</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="card-surface p-10 text-center">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 mx-auto flex items-center justify-center mb-3">
              <ArrowUpRight className="w-8 h-8 text-slate-400" aria-hidden="true" />
            </div>
            <p className="font-display font-bold text-mtn-dark">{t('transactions.no_transactions')}</p>
          </div>
        ) : (
          <div className="space-y-2" role="list" aria-label={t('transactions.title')}>
            {filtered.map((txn, idx) => {
              const isIn = txn.direction === 'in'
              return (
                <div
                  key={txn.id}
                  role="listitem"
                  className={`group card-surface p-3 sm:p-3.5 lift animate-slide-up ${txn.is_flagged ? 'border-red-200 bg-gradient-to-br from-white to-red-50/40' : ''}`}
                  style={{ animationDelay: `${Math.min(idx * 40, 320)}ms` }}
                  aria-label={`${isIn ? t('transactions.incoming') : t('transactions.outgoing')}: R${txn.amount} - ${txn.counterparty_name || txn.category}`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`relative w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0 ${
                      isIn
                        ? 'bg-gradient-to-br from-emerald-400 to-emerald-600 text-white shadow-soft'
                        : 'bg-gradient-to-br from-rose-400 to-rose-600 text-white shadow-soft'
                    }`} aria-hidden="true">
                      {isIn ? <ArrowDownLeft className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-slate-800 truncate">
                          {txn.counterparty_name || txn.counterparty_phone || txn.category}
                        </p>
                        {getRiskBadge(txn.risk_level)}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5">
                        <time dateTime={txn.timestamp}>{new Date(txn.timestamp).toLocaleDateString()}</time>
                        <span className="w-1 h-1 rounded-full bg-slate-300" aria-hidden="true" />
                        <span className="capitalize">{txn.category?.replace('_', ' ')}</span>
                      </p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className={`font-display font-bold text-base ${isIn ? 'text-emerald-600' : 'text-slate-900'}`}>
                        {isIn ? '+' : '-'}R{txn.amount.toLocaleString()}
                      </p>
                    </div>
                  </div>
                  {txn.risk_reason && (
                    <div className="mt-2 ml-14 px-3 py-2 rounded-xl bg-red-50 border border-red-100">
                      <p className="text-xs text-red-600 flex items-start gap-1.5" role="alert">
                        <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" aria-hidden="true" />
                        <span>{txn.risk_reason}</span>
                      </p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}