import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import api from '../services/api'

const GIS_SRC = 'https://accounts.google.com/gsi/client'

/**
 * "Sign in with Google" button built on Google Identity Services.
 *
 * The GIS library is loaded once on mount. The button is disabled until GIS is
 * ready and a VITE_GOOGLE_CLIENT_ID is configured. On click, the returned ID
 * token is POSTed to /api/auth/google for verification and JWT exchange.
 */
export default function GoogleSignIn({ onLogin, onError }) {
  const { t } = useTranslation()
  const buttonRef = useRef(null)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

  useEffect(() => {
    if (!clientId) return
    let cancelled = false

    const onReady = () => {
      if (cancelled || !window.google?.accounts?.id) return
      try {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
        })
        if (buttonRef.current) {
          window.google.accounts.id.renderButton(buttonRef.current, {
            type: 'standard',
            theme: 'outline',
            size: 'large',
            text: 'continue_with',
            shape: 'pill',
            logo_alignment: 'left',
            width: 320,
          })
        }
        setReady(true)
      } catch (err) {
        setError('Google sign-in could not initialise.')
        onError?.(err)
      }
    }

    if (window.google?.accounts?.id) {
      onReady()
    } else {
      const script = document.createElement('script')
      script.src = GIS_SRC
      script.async = true
      script.defer = true
      script.onload = onReady
      script.onerror = () => setError('Could not load Google sign-in.')
      document.head.appendChild(script)
    }

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId])

  async function handleCredentialResponse(response) {
    setError('')
    setBusy(true)
    try {
      const { data } = await api.post('/api/auth/google', { credential: response.credential })
      onLogin?.(data.user, data.access_token)
    } catch (err) {
      const detail = err.response?.data?.detail || t('common.error')
      setError(detail)
      onError?.(err)
    } finally {
      setBusy(false)
    }
  }

  if (!clientId) {
    return (
      <p className="text-xs text-slate-500 text-center" role="status">
        Google sign-in is not configured. Set <code className="font-mono">VITE_GOOGLE_CLIENT_ID</code> in <code className="font-mono">frontend/.env</code>.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      <div
        ref={buttonRef}
        className={`flex justify-center ${ready ? '' : 'opacity-50 pointer-events-none'}`}
        aria-label="Sign in with Google"
      />
      {!ready && !error && (
        <p className="text-xs text-slate-500 text-center" role="status">Loading Google sign-in…</p>
      )}
      {busy && (
        <p className="text-xs text-slate-500 text-center" role="status">Signing you in…</p>
      )}
      {error && (
        <p className="text-xs text-red-600 text-center" role="alert" aria-live="assertive">{error}</p>
      )}
    </div>
  )
}