import { useState, useEffect } from 'react'
import { Users, Plus, ArrowRight } from 'lucide-react'
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
      announce(t('a11y.error_occurred'), 'assertive')
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

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-mtn-dark">{t('stokvel.title')}</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1 bg-mtn-yellow text-mtn-blue text-sm font-semibold px-3 py-2 rounded-lg focus-visible:ring-2 focus-visible:ring-mtn-blue focus:outline-none"
          aria-label={t('stokvel.new')}
        >
          <Plus className="w-4 h-4" aria-hidden="true" /> {t('stokvel.new')}
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <form onSubmit={createStokvel} className="bg-white rounded-xl p-4 shadow-sm space-y-3" aria-label={t('stokvel.create')}>
          <div>
            <label htmlFor="stokvel-name" className="sr-only">{t('stokvel.name_label')}</label>
            <input
              id="stokvel-name"
              placeholder={t('stokvel.name_label')}
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-mtn-yellow outline-none"
              required
            />
          </div>
          <div>
            <label htmlFor="stokvel-amount" className="sr-only">{t('stokvel.contribution_label')}</label>
            <input
              id="stokvel-amount"
              type="number"
              placeholder={t('stokvel.contribution_label')}
              value={form.contribution_amount}
              onChange={(e) => setForm({ ...form, contribution_amount: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-mtn-yellow outline-none"
              required
              inputMode="decimal"
            />
          </div>
          <div>
            <label htmlFor="stokvel-frequency" className="sr-only">{t('stokvel.frequency_label')}</label>
            <select
              id="stokvel-frequency"
              value={form.frequency}
              onChange={(e) => setForm({ ...form, frequency: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-mtn-yellow outline-none"
            >
              <option value="weekly">{t('stokvel.weekly')}</option>
              <option value="biweekly">{t('stokvel.biweekly')}</option>
              <option value="monthly">{t('stokvel.monthly')}</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="flex-1 bg-mtn-blue text-white py-2 rounded-lg text-sm font-medium focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none">
              {t('stokvel.create')}
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="flex-1 border py-2 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none">
              {t('common.cancel')}
            </button>
          </div>
        </form>
      )}

      {/* Stokvel List */}
      {loading ? (
        <div className="text-center text-gray-400 py-8" role="status">{t('common.loading')}</div>
      ) : stokvels.length === 0 ? (
        <div className="text-center py-12">
          <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" aria-hidden="true" />
          <p className="text-gray-500">{t('stokvel.no_stokvels')}</p>
        </div>
      ) : (
        <div role="list" aria-label={t('stokvel.title')}>
          {stokvels.map((s) => (
            <div key={s.id} className="bg-white rounded-xl p-4 shadow-sm mb-3" role="listitem">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-mtn-dark">{s.name}</h3>
                  <p className="text-sm text-gray-500">
                    R{s.contribution_amount} / {t(`stokvel.${s.frequency}`)} • {s.member_count} {t('stokvel.members')}
                  </p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100'}`}>
                  {s.is_active ? t('stokvel.active') : t('stokvel.paused')}
                </span>
              </div>
              <button
                onClick={() => contribute(s.id)}
                className="mt-3 flex items-center gap-1 text-sm text-mtn-blue font-medium focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none rounded px-1"
                aria-label={`${t('stokvel.record_contribution')} - ${s.name}`}
              >
                {t('stokvel.record_contribution')} <ArrowRight className="w-3 h-3" aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
