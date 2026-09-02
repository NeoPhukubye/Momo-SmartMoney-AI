import { useState, useEffect } from 'react'
import { ArrowUpRight, ArrowDownLeft, AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import api from '../services/api'

export default function Transactions() {
  const { t } = useTranslation()
  const { announce } = useAccessibility()
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

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
    if (filter === 'income') return txn.direction === 'in'
    if (filter === 'expenses') return txn.direction === 'out'
    if (filter === 'flagged') return txn.is_flagged
    return true
  })

  const getRiskBadge = (level) => {
    const colors = {
      low: '',
      medium: 'bg-yellow-100 text-yellow-700',
      high: 'bg-orange-100 text-orange-700',
      critical: 'bg-red-100 text-red-700',
    }
    if (level === 'low') return null
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full ${colors[level]}`} role="status">
        <AlertTriangle className="w-3 h-3 inline mr-1" aria-hidden="true" />
        {t(`transactions.risk_${level}`)}
      </span>
    )
  }

  if (loading) {
    return <div className="text-center py-8 text-gray-400" role="status" aria-label={t('common.loading')}>{t('common.loading')}</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-mtn-dark">{t('transactions.title')}</h2>

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label={t('common.filter')}>
        {['all', 'income', 'expenses', 'flagged'].map((f) => (
          <button
            key={f}
            role="tab"
            aria-selected={filter === f}
            aria-controls="transactions-list"
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none ${
              filter === f ? 'bg-mtn-blue text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {t(`transactions.filter_${f}`)}
          </button>
        ))}
      </div>

      {/* Transaction List */}
      <div id="transactions-list" role="tabpanel">
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            {t('transactions.no_transactions')}
          </div>
        ) : (
          <div className="space-y-2" role="list" aria-label={t('transactions.title')}>
            {filtered.map((txn) => (
              <div
                key={txn.id}
                className={`bg-white rounded-xl p-3 shadow-sm ${txn.is_flagged ? 'border border-red-200' : ''}`}
                role="listitem"
                aria-label={`${txn.direction === 'in' ? t('transactions.incoming') : t('transactions.outgoing')}: R${txn.amount} - ${txn.counterparty_name || txn.category}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      txn.direction === 'in' ? 'bg-green-100' : 'bg-red-50'
                    }`} aria-hidden="true">
                      {txn.direction === 'in' ? (
                        <ArrowDownLeft className="w-4 h-4 text-green-600" />
                      ) : (
                        <ArrowUpRight className="w-4 h-4 text-red-500" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {txn.counterparty_name || txn.counterparty_phone || txn.category}
                      </p>
                      <p className="text-xs text-gray-400">
                        <time dateTime={txn.timestamp}>{new Date(txn.timestamp).toLocaleDateString()}</time> • {txn.category}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-bold ${txn.direction === 'in' ? 'text-green-600' : 'text-gray-800'}`}>
                      {txn.direction === 'in' ? '+' : '-'}R{txn.amount.toLocaleString()}
                    </p>
                    {getRiskBadge(txn.risk_level)}
                  </div>
                </div>
                {txn.risk_reason && (
                  <p className="text-xs text-red-500 mt-2 pl-11" role="alert">{txn.risk_reason}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
