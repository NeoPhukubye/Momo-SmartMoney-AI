import { useState } from 'react'
import { Shield, Phone, Lock, User as UserIcon, Sparkles, ArrowRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import LanguageSwitcher from '../components/LanguageSwitcher'
import GoogleSignIn from '../components/GoogleSignIn'
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

  const bgClass = settings.darkMode ? 'bg-mesh-dark' : 'bg-mesh-light'

  return (
    <div className={`min-h-screen relative overflow-hidden ${bgClass}`}>
      {/* Decorative orbs */}
      <div className="pointer-events-none absolute -top-32 -left-24 w-80 h-80 rounded-full bg-mtn-yellow/30 blur-3xl" aria-hidden="true" />
      <div className="pointer-events-none absolute top-1/3 -right-24 w-96 h-96 rounded-full bg-mtn-blue/20 blur-3xl" aria-hidden="true" />

      <div className="relative min-h-screen flex flex-col">
        {/* Top bar */}
        <div className="flex items-center justify-between p-5">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-mtn-yellow to-mtn-yellow-deep flex items-center justify-center shadow-glow-yellow">
              <Shield className="w-5 h-5 text-mtn-blue-deep" aria-hidden="true" />
            </div>
            <div className="leading-tight">
              <p className="font-display font-extrabold text-mtn-blue text-lg tracking-tight">SmartMoney</p>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-mtn-blue/60">AI Coach</p>
            </div>
          </div>
          <LanguageSwitcher />
        </div>

        {/* Hero */}
        <div className="px-6 pt-6 pb-4 max-w-md w-full mx-auto animate-fade-in">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/70 backdrop-blur border border-white/60 shadow-soft text-[11px] font-semibold text-mtn-blue mb-4">
            <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Your pocket financial coach</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-extrabold tracking-tight text-mtn-blue leading-[1.05]">
            Spend smarter.<br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-mtn-yellow-deep via-mtn-yellow to-mtn-yellow-deep">
              Save together.
            </span>
          </h1>
          <p className="mt-3 text-sm text-slate-600 max-w-sm">{t('auth.tagline')}</p>
        </div>

        {/* Form card */}
        <div className="flex-1 px-5 pb-8 max-w-md w-full mx-auto w-full">
          <div className="card-surface p-6 sm:p-7 animate-slide-up shadow-lift">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-display text-xl font-bold text-mtn-dark">
                {isRegister ? t('auth.create_account') : t('auth.welcome_back')}
              </h2>
              <div className="text-[10px] font-semibold uppercase tracking-widest text-mtn-blue/60">
                {isRegister ? 'Step 1 of 1' : 'Sign in'}
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4" aria-label={isRegister ? t('auth.create_account') : t('auth.welcome_back')}>
              {isRegister && (
                <Field
                  id="name"
                  label={t('auth.full_name')}
                  icon={UserIcon}
                  type="text"
                  value={name}
                  onChange={setName}
                  placeholder={t('auth.name_placeholder')}
                  autoComplete="name"
                />
              )}

              <Field
                id="phone"
                label={t('auth.phone_number')}
                icon={Phone}
                type="tel"
                value={phone}
                onChange={setPhone}
                placeholder={t('auth.phone_placeholder')}
                autoComplete="tel"
                inputMode="tel"
              />

              <Field
                id="pin"
                label={t('auth.pin')}
                icon={Lock}
                type="password"
                value={pin}
                onChange={setPin}
                placeholder={t('auth.enter_pin')}
                maxLength={4}
                autoComplete="current-password"
                inputMode="numeric"
                pattern="[0-9]{4}"
              />

              {error && (
                <div className="flex items-start gap-2 px-3 py-2.5 rounded-xl bg-red-50 border border-red-100" role="alert" aria-live="assertive">
                  <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" aria-hidden="true" />
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="group relative w-full overflow-hidden rounded-2xl bg-gradient-to-r from-mtn-yellow to-mtn-yellow-deep text-mtn-blue-deep font-extrabold py-3.5 px-4 shadow-glow-yellow hover:shadow-lift disabled:opacity-60 disabled:cursor-not-allowed transition-all focus-visible:ring-4 focus-visible:ring-mtn-blue/30 focus:outline-none"
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {loading ? (
                    <>
                      <Spinner /> {t('auth.please_wait')}
                    </>
                  ) : (
                    <>
                      {isRegister ? t('auth.create_account') : t('common.login')}
                      <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                    </>
                  )}
                </span>
                <span className="absolute inset-0 shimmer-bg opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden="true" />
              </button>

              <div className="mt-3 flex items-center gap-3" aria-hidden="true">
                <span className="flex-1 h-px bg-slate-200" />
                <span className="text-[10px] uppercase tracking-widest text-slate-400 font-semibold">or continue with Google</span>
                <span className="flex-1 h-px bg-slate-200" />
              </div>

              <div className="pt-1">
                <GoogleSignIn
                  onLogin={onLogin}
                  onError={(err) => setError(err.response?.data?.detail || t('common.error'))}
                />
              </div>

              <p className="text-center text-sm text-slate-500 pt-1">
                {isRegister ? t('auth.already_have_account') : t('auth.no_account')}{' '}
                <button
                  type="button"
                  onClick={() => setIsRegister(!isRegister)}
                  className="text-mtn-blue font-semibold hover:text-mtn-blue-light focus-visible:underline focus:outline-none"
                >
                  {isRegister ? t('common.login') : t('auth.register')}
                </button>
              </p>
            </form>
          </div>

          {/* Trust strip */}
          <div className="mt-6 grid grid-cols-3 gap-2 text-center animate-fade-in">
            {[
              { k: 'Bank-grade', v: 'security' },
              { k: '16', v: 'languages' },
              { k: 'AI', v: 'coaching' },
            ].map((it) => (
              <div key={it.k} className="rounded-2xl bg-white/60 backdrop-blur border border-white/60 px-3 py-2.5">
                <p className="font-display font-bold text-mtn-blue text-sm">{it.k}</p>
                <p className="text-[10px] uppercase tracking-widest text-slate-500">{it.v}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function Field({ id, label, icon: Icon, type = 'text', value, onChange, placeholder, ...rest }) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">
        {label}
      </label>
      <div className="relative group">
        <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-mtn-blue transition" aria-hidden="true">
          <Icon className="w-4 h-4" />
        </span>
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full pl-11 pr-3 py-3 rounded-2xl bg-white border border-slate-200 text-sm text-slate-800 placeholder:text-slate-400 focus:bg-white focus:border-mtn-blue focus:ring-4 focus:ring-mtn-blue/10 outline-none transition"
          {...rest}
        />
      </div>
    </div>
  )
}

function Spinner() {
  return (
    <span className="inline-block w-4 h-4 border-2 border-mtn-blue-deep/30 border-t-mtn-blue-deep rounded-full animate-spin" aria-hidden="true" />
  )
}