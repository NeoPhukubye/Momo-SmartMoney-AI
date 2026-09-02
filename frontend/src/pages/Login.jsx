import { useState } from 'react'
import { Shield, Phone } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import LanguageSwitcher from '../components/LanguageSwitcher'
import api from '../services/api'

export default function Login({ onLogin }) {
  const { t } = useTranslation()
  const { settings } = useAccessibility()
  const [isRegister, setIsRegister] = useState(false)
  const [phone, setPhone] = useState('')
  const [name, setName] = useState('')
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login'
      const payload = isRegister
        ? { phone_number: phone, name, pin }
        : { phone_number: phone, pin }

      const { data } = await api.post(endpoint, payload)
      onLogin(data.user, data.access_token)
    } catch (err) {
      setError(err.response?.data?.detail || t('common.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`min-h-screen flex items-center justify-center p-4 ${settings.darkMode ? 'bg-gray-900' : 'bg-mtn-light'}`}>
      <div className="w-full max-w-sm">
        {/* Language Switcher at top */}
        <div className="flex justify-end mb-4">
          <LanguageSwitcher />
        </div>

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-mtn-yellow rounded-full mb-3">
            <Shield className="w-8 h-8 text-mtn-blue" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-mtn-dark">{t('common.home') === 'Home' ? 'SmartMoney AI' : 'SmartMoney AI'}</h1>
          <p className={`text-sm mt-1 ${settings.darkMode ? 'text-gray-400' : 'text-gray-500'}`}>{t('auth.tagline')}</p>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className={`rounded-xl p-6 shadow-sm space-y-4 ${settings.darkMode ? 'bg-gray-800' : 'bg-white'}`}
          aria-label={isRegister ? t('auth.create_account') : t('auth.welcome_back')}
        >
          <h2 className="text-lg font-semibold text-center">
            {isRegister ? t('auth.create_account') : t('auth.welcome_back')}
          </h2>

          {isRegister && (
            <div>
              <label htmlFor="name" className={`text-sm ${settings.darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                {t('auth.full_name')}
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t('auth.name_placeholder')}
                className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-mtn-yellow outline-none"
                required
                autoComplete="name"
              />
            </div>
          )}

          <div>
            <label htmlFor="phone" className={`text-sm ${settings.darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              {t('auth.phone_number')}
            </label>
            <div className="flex items-center gap-2 mt-1">
              <Phone className="w-4 h-4 text-gray-400" aria-hidden="true" />
              <input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder={t('auth.phone_placeholder')}
                className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-mtn-yellow outline-none"
                required
                autoComplete="tel"
                inputMode="tel"
              />
            </div>
          </div>

          <div>
            <label htmlFor="pin" className={`text-sm ${settings.darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              {t('auth.pin')}
            </label>
            <input
              id="pin"
              type="password"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder={t('auth.enter_pin')}
              maxLength={4}
              className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-mtn-yellow outline-none"
              required
              autoComplete="current-password"
              inputMode="numeric"
              pattern="[0-9]{4}"
            />
          </div>

          {error && (
            <p className="text-red-500 text-sm" role="alert" aria-live="assertive">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-mtn-yellow text-mtn-blue font-bold py-3 rounded-lg hover:bg-yellow-400 disabled:opacity-50 transition focus-visible:ring-2 focus-visible:ring-mtn-blue focus:outline-none"
          >
            {loading ? t('auth.please_wait') : isRegister ? t('auth.create_account') : t('common.login')}
          </button>

          <p className="text-center text-sm text-gray-500">
            {isRegister ? t('auth.already_have_account') : t('auth.no_account')}{' '}
            <button
              type="button"
              onClick={() => setIsRegister(!isRegister)}
              className="text-mtn-blue font-medium focus-visible:underline focus:outline-none"
            >
              {isRegister ? t('common.login') : t('auth.register')}
            </button>
          </p>
        </form>
      </div>
    </div>
  )
}
