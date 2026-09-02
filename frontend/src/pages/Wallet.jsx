import { useState, useEffect, useRef } from 'react'
import {
  Wallet as WalletIcon,
  ArrowDownLeft,
  ArrowUpRight,
  Send,
  ArrowLeftRight,
  QrCode,
  ScanLine,
  X,
  RefreshCw,
  CreditCard,
  ShieldCheck,
  Copy,
  Hash,
  Phone,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import api from '../services/api'
import QRScanner from '../components/QRScanner'
import QRGenerator from '../components/QRGenerator'

const TONE = {
  deposit: { Icon: ArrowDownLeft, label: 'Top-up', cls: 'text-emerald-700 bg-emerald-50 border-emerald-100' },
  transfer_in: { Icon: ArrowDownLeft, label: 'Received', cls: 'text-emerald-700 bg-emerald-50 border-emerald-100' },
  withdrawal: { Icon: ArrowUpRight, label: 'Withdraw', cls: 'text-rose-700 bg-rose-50 border-rose-100' },
  transfer_out: { Icon: ArrowUpRight, label: 'Sent', cls: 'text-rose-700 bg-rose-50 border-rose-100' },
  stokvel_contribution: { Icon: ShieldCheck, label: 'Stokvel', cls: 'text-violet-700 bg-violet-50 border-violet-100' },
  fee: { Icon: ArrowUpRight, label: 'Fee', cls: 'text-slate-700 bg-slate-50 border-slate-100' },
}

const USSD_CODE = '*141*8#'

export default function Wallet() {
  const { t } = useTranslation()
  const { announce } = useAccessibility()
  const [wallet, setWallet] = useState(null)
  const [txns, setTxns] = useState([])
  const [loading, setLoading] = useState(true)
  const [action, setAction] = useState(null) // 'deposit' | 'withdraw' | 'send' | 'request' | 'scan' | 'myqr' | 'ussd' | null
  const [amount, setAmount] = useState('')
  const [phone, setPhone] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [scanResult, setScanResult] = useState(null)
  const [myRequests, setMyRequests] = useState([])
  const [lastRequest, setLastRequest] = useState(null)
  const [gpayBusy, setGpayBusy] = useState(false)
  const [gpayMessage, setGpayMessage] = useState('')
  const pollersRef = useRef({})

  const loadAll = async () => {
    try {
      const [w, t, r] = await Promise.all([
        api.get('/api/wallet'),
        api.get('/api/wallet/transactions'),
        api.get('/api/wallet/request/me').catch(() => ({ data: [] })),
      ])
      setWallet(w.data)
      setTxns(t.data)
      setMyRequests(r.data)
    } catch (err) {
      announce(t('a11y.error_occurred'), 'assertive')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadAll() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Poll pending MoMo-backed deposits/withdrawals
  useEffect(() => {
    txns.forEach((txn) => {
      if (txn.status !== 'pending' || pollersRef.current[txn.id]) return
      const handle = setInterval(async () => {
        try {
          const { data } = await api.post(`/api/wallet/transactions/${txn.id}/sync`)
          if (data.status !== 'pending') {
            clearInterval(handle)
            delete pollersRef.current[txn.id]
            announce(`Transaction ${data.status}`)
            loadAll()
          }
        } catch (err) {
          clearInterval(handle)
          delete pollersRef.current[txn.id]
        }
      }, 6000)
      pollersRef.current[txn.id] = handle
    })
    return () => {
      Object.values(pollersRef.current).forEach(clearInterval)
    }
  }, [txns]) // eslint-disable-line react-hooks/exhaustive-deps

  const submitMoMoAction = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const value = parseFloat(amount)
      if (!value || value <= 0) throw new Error('Enter a valid amount')
      const endpoint = action === 'deposit' ? '/api/wallet/deposit' : '/api/wallet/withdraw'
      await api.post(endpoint, { amount: value, phone, note })
      setAmount(''); setPhone(''); setNote('')
      setAction(null)
      announce(`${action === 'deposit' ? 'Top-up' : 'Withdrawal'} initiated`)
      await loadAll()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || t('common.error'))
    } finally {
      setBusy(false)
    }
  }

  const submitSend = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const value = parseFloat(amount)
      if (!value || value <= 0) throw new Error('Enter a valid amount')
      if (!phone) throw new Error('Recipient phone is required')
      await api.post('/api/wallet/send', { amount: value, recipient_phone: phone, note })
      setAmount(''); setPhone(''); setNote('')
      setAction(null)
      announce('Money sent')
      await loadAll()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || t('common.error'))
    } finally {
      setBusy(false)
    }
  }

  const submitRequest = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const value = parseFloat(amount)
      if (!value || value <= 0) throw new Error('Enter a valid amount')
      const { data } = await api.post('/api/wallet/request', { amount: value, note })
      setLastRequest(data)
      setAmount(''); setNote('')
      announce('Request created')
      await loadAll()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || t('common.error'))
    } finally {
      setBusy(false)
    }
  }

  const payRequest = async (code) => {
    setError('')
    setBusy(true)
    try {
      await api.post(`/api/wallet/request/${code}/pay`)
      announce('Payment sent')
      setScanResult(null)
      await loadAll()
    } catch (err) {
      setError(err.response?.data?.detail || t('common.error'))
    } finally {
      setBusy(false)
    }
  }

  const handleScanResult = (result) => {
    setScanResult(result)
    if (result?.phone) setPhone(result.phone)
    if (result?.amount) setAmount(String(result.amount))
    // Auto-route: payment requests → offer to pay
    if (result?.reference && /^[A-Z0-9]{6,12}$/.test(result.reference)) {
      // Could be a payment request or a stokvel invite; show both
    }
  }

  const enrolGoogleWallet = async () => {
    setGpayBusy(true)
    setGpayMessage('')
    try {
      const { data } = await api.post('/api/wallet/google-wallet/enrol', { display_name: 'SmartMoney MoMo Card' })
      setGpayMessage(data.save_url)
      window.open(data.save_url, '_blank', 'noopener,noreferrer')
    } catch (err) {
      setGpayMessage('Could not create Google Wallet save link.')
    } finally {
      setGpayBusy(false)
    }
  }

  const copyUssd = () => {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(USSD_CODE)
      announce('USSD code copied')
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl p-5 sm:p-6 text-white shadow-lift bg-night-sheen">
        <div className="absolute -top-16 -right-12 w-56 h-56 rounded-full bg-mtn-yellow/25 blur-3xl pointer-events-none" aria-hidden="true" />
        <div className="absolute -bottom-20 -left-12 w-56 h-56 rounded-full bg-mtn-blue-light/30 blur-3xl pointer-events-none" aria-hidden="true" />

        <div className="relative">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-white/15 backdrop-blur flex items-center justify-center" aria-hidden="true">
                <WalletIcon className="w-4 h-4 text-mtn-yellow" />
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.18em] text-white/60 font-semibold">My Wallet</p>
                <p className="text-xs text-white/70">MoMo • Google Wallet • USSD</p>
              </div>
            </div>
            {wallet?.google_wallet_object_id ? (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-400/20 text-emerald-100 backdrop-blur flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> Google Wallet
              </span>
            ) : (
              <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-white/10 text-white/80 backdrop-blur">Virtual</span>
            )}
          </div>

          <p className="font-display text-4xl sm:text-5xl font-extrabold tracking-tight" aria-label={`Balance: R${(wallet?.balance || 0).toLocaleString()}`}>
            R{(wallet?.balance || 0).toLocaleString()}
          </p>
          <p className="text-xs text-white/60 mt-1">{wallet?.currency || 'ZAR'} • available balance</p>

          <div className="mt-5 grid grid-cols-4 gap-2">
            <ActionButton icon={ArrowLeftRight} label="Send" onClick={() => { setAction('send'); setError('') }} />
            <ActionButton icon={QrCode} label="Request" onClick={() => { setAction('request'); setError('') }} />
            <ActionButton icon={ScanLine} label="Scan" onClick={() => { setAction('scan'); setError('') }} />
            <ActionButton icon={ArrowDownLeft} label="Top up" onClick={() => { setAction('deposit'); setError('') }} />
          </div>
        </div>
      </section>

      {/* USSD quick-dial */}
      <section className="card-surface p-4">
        <div className="flex items-start gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-mtn-yellow to-mtn-yellow-deep flex items-center justify-center flex-shrink-0" aria-hidden="true">
            <Hash className="w-5 h-5 text-mtn-blue-deep" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-display font-bold text-mtn-dark">Use *141*8# from any phone</h3>
            <p className="text-xs text-slate-500 mt-0.5">Check balance, send money, join a Stokvel — no internet needed.</p>
            <div className="mt-2 flex items-center gap-2">
              <code className="px-3 py-1.5 rounded-xl bg-mtn-blue text-white font-display font-bold text-base tracking-wider">{USSD_CODE}</code>
              <button
                type="button"
                onClick={copyUssd}
                className="inline-flex items-center gap-1 text-xs font-semibold text-mtn-blue hover:text-mtn-blue-light focus-visible:underline focus:outline-none rounded px-2 py-1.5"
                aria-label={`Copy ${USSD_CODE}`}
              >
                <Copy className="w-3.5 h-3.5" /> Copy
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Google Wallet enrolment */}
      <section className="card-surface p-4 sm:p-5">
        <div className="flex items-start gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-700 flex items-center justify-center flex-shrink-0" aria-hidden="true">
            <CreditCard className="w-5 h-5 text-mtn-yellow" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-display font-bold text-mtn-dark">Add to Google Wallet</h3>
            <p className="text-xs text-slate-500 mt-0.5">Tap-to-pay with your SmartMoney MoMo card on any contactless POS.</p>
          </div>
        </div>
        <button
          type="button"
          onClick={enrolGoogleWallet}
          disabled={gpayBusy}
          className="mt-3 w-full inline-flex items-center justify-center gap-2 rounded-2xl bg-neutral-900 text-white font-semibold py-2.5 px-4 hover:bg-black transition shadow-soft disabled:opacity-60 focus-visible:ring-4 focus-visible:ring-mtn-yellow/30 focus:outline-none"
        >
          <img src="https://www.gstatic.com/instantbuy/svg/dark_gpay.svg" alt="Google Pay" className="h-5" />
          <span>{gpayBusy ? 'Preparing…' : wallet?.google_wallet_object_id ? 'Re-add to Google Wallet' : 'Add to Google Wallet'}</span>
        </button>
        {gpayMessage && (
          <p className="mt-2 text-xs text-slate-500 break-all" role="status">
            Save link: <a className="text-mtn-blue underline" href={gpayMessage} target="_blank" rel="noreferrer">{gpayMessage}</a>
          </p>
        )}
      </section>

      {/* Action modals */}
      {action === 'send' && (
        <Modal title="Send money" subtitle="Instant transfer to another SmartMoney user." onClose={() => { setAction(null); setError('') }}>
          <Form
            onSubmit={submitSend}
            busy={busy}
            error={error}
            amount={amount} setAmount={setAmount}
            phone={phone} setPhone={setPhone} phoneLabel="Recipient phone (must be a SmartMoney user)"
            note={note} setNote={setNote}
            submitLabel="Send now"
            submitIcon={Send}
          />
        </Modal>
      )}

      {action === 'request' && (
        <Modal title="Request money" subtitle="Create a QR code for someone to scan and pay you." onClose={() => { setAction(null); setError(''); setLastRequest(null) }}>
          {!lastRequest ? (
            <form onSubmit={submitRequest} className="space-y-3" aria-label="Request money">
              <div>
                <label htmlFor="rq-amount" className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">Amount (ZAR)</label>
                <input id="rq-amount" type="number" inputMode="decimal" min="1" step="0.01" required value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:border-mtn-blue focus:ring-4 focus:ring-mtn-blue/10 outline-none transition" />
              </div>
              <div>
                <label htmlFor="rq-note" className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">What's it for?</label>
                <input id="rq-note" type="text" value={note} onChange={(e) => setNote(e.target.value)} className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:border-mtn-blue focus:ring-4 focus:ring-mtn-blue/10 outline-none transition" />
              </div>
              {error && <ErrorBox message={error} />}
              <SubmitRow busy={busy} onCancel={() => { setAction(null); setError('') }} label="Create request" icon={QrCode} />
            </form>
          ) : (
            <div className="space-y-3 text-center">
              <p className="text-sm text-slate-500">Share this QR or the 8-character code below.</p>
              <QRGenerator payload={lastRequest.qr_payload} label={lastRequest.code} size={200} />
              <p className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Code</p>
              <p className="font-display text-2xl font-extrabold text-mtn-blue tracking-widest">{lastRequest.code}</p>
              <button
                type="button"
                onClick={() => { setAction(null); setLastRequest(null) }}
                className="w-full bg-slate-100 text-slate-700 font-semibold py-3 rounded-2xl hover:bg-slate-200 transition"
              >
                Done
              </button>
            </div>
          )}
        </Modal>
      )}

      {action === 'deposit' && (
        <Modal title="Top up via MoMo" subtitle="We'll request a payment to your mobile money number." onClose={() => { setAction(null); setError('') }}>
          <Form
            onSubmit={submitMoMoAction}
            busy={busy}
            error={error}
            amount={amount} setAmount={setAmount}
            phone={phone} setPhone={setPhone} phoneLabel="Your MoMo number"
            note={note} setNote={setNote}
            submitLabel="Request top-up"
            submitIcon={ArrowDownLeft}
          />
        </Modal>
      )}

      {action === 'withdraw' && (
        <Modal title="Withdraw to MoMo" subtitle="Move money from your wallet back to your MoMo number." onClose={() => { setAction(null); setError('') }}>
          <Form
            onSubmit={submitMoMoAction}
            busy={busy}
            error={error}
            amount={amount} setAmount={setAmount}
            phone={phone} setPhone={setPhone} phoneLabel="Your MoMo number"
            note={note} setNote={setNote}
            submitLabel="Request withdrawal"
            submitIcon={ArrowUpRight}
          />
        </Modal>
      )}

      {action === 'scan' && (
        <Modal title="Scan a QR" subtitle="MoMo, payment request, or Stokvel invite." onClose={() => { setAction(null); setScanResult(null); setError('') }}>
          <QRScanner onResult={handleScanResult} onClose={() => { setAction(null); setScanResult(null) }} />
          {error && <div className="mt-3"><ErrorBox message={error} /></div>}
          {scanResult && (
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3" role="status">
              <p className="text-[11px] uppercase tracking-widest text-slate-500 font-semibold">Detected</p>
              <p className="text-sm font-semibold text-mtn-dark mt-0.5">{scanResult.kind}</p>
              {scanResult.amount && <p className="text-xs text-slate-600">Amount: R{scanResult.amount}</p>}
              {scanResult.phone && <p className="text-xs text-slate-600">Phone: {scanResult.phone}</p>}
              {scanResult.payee_name && <p className="text-xs text-slate-600">Payee: {scanResult.payee_name}</p>}
              {scanResult.reference && <p className="text-xs text-slate-600">Reference: {scanResult.reference}</p>}
              {scanResult.kind === 'momo_pay' && scanResult.reference && /^[A-Z0-9]{6,12}$/.test(scanResult.reference) && (
                <button
                  type="button"
                  onClick={() => payRequest(scanResult.reference)}
                  disabled={busy}
                  className="mt-2 inline-flex items-center gap-1 text-xs font-bold text-white bg-mtn-blue px-3 py-1.5 rounded-xl focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
                >
                  Pay this request ({scanResult.amount ? `R${scanResult.amount}` : ''})
                </button>
              )}
            </div>
          )}
        </Modal>
      )}

      {/* Open payment requests */}
      {myRequests.filter((r) => r.status === 'open').length > 0 && (
        <section>
          <h3 className="font-display font-bold text-mtn-dark mb-2.5 px-1">Open requests</h3>
          <div className="space-y-2">
            {myRequests.filter((r) => r.status === 'open').map((r) => (
              <div key={r.id} className="card-surface p-3.5 flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center flex-shrink-0" aria-hidden="true">
                  <QrCode className="w-4 h-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-800">R{r.amount.toLocaleString()}</p>
                  <p className="text-xs text-slate-500">Code {r.code}{r.note ? ` • ${r.note}` : ''}</p>
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">Open</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Transactions */}
      <section>
        <div className="flex items-center justify-between mb-2.5 px-1">
          <h3 className="font-display font-bold text-mtn-dark">Recent activity</h3>
          <button type="button" onClick={loadAll} className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-mtn-blue focus-visible:underline focus:outline-none rounded px-1.5 py-1" aria-label="Refresh">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>
        {loading ? (
          <div className="space-y-2" role="status" aria-label={t('common.loading')}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 rounded-2xl bg-slate-100 animate-pulse" aria-hidden="true" />
            ))}
            <span className="sr-only">{t('common.loading')}</span>
          </div>
        ) : txns.length === 0 ? (
          <div className="card-surface p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 mx-auto flex items-center justify-center mb-3">
              <WalletIcon className="w-7 h-7 text-slate-400" aria-hidden="true" />
            </div>
            <p className="font-display font-bold text-mtn-dark">No transactions yet</p>
            <p className="text-sm text-slate-500 mt-1">Send, request, or scan to get started.</p>
          </div>
        ) : (
          <div className="space-y-2" role="list" aria-label="Wallet transactions">
            {txns.map((txn) => {
              const cfg = TONE[txn.type] || TONE.deposit
              const { Icon } = cfg
              const positive = txn.type === 'deposit' || txn.type === 'transfer_in'
              return (
                <div key={txn.id} role="listitem" className="card-surface p-3.5 lift animate-slide-up" aria-label={`${cfg.label} of R${txn.amount} ${txn.status}`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 ${cfg.cls}`} aria-hidden="true">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-slate-800 truncate">
                        {cfg.label}{txn.counterparty_name ? ` • ${txn.counterparty_name}` : txn.counterparty_phone ? ` • ${txn.counterparty_phone}` : ''}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5">
                        <time>{new Date(txn.created_at).toLocaleString()}</time>
                        <span className="w-1 h-1 rounded-full bg-slate-300" />
                        <span className={txn.status === 'pending' ? 'text-amber-700' : txn.status === 'failed' ? 'text-rose-700' : 'text-emerald-700'}>
                          {txn.status}
                        </span>
                      </p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className={`font-display font-bold ${positive ? 'text-emerald-700' : 'text-slate-900'}`}>
                        {positive ? '+' : '-'}R{txn.amount.toLocaleString()}
                      </p>
                      {txn.reference && <p className="text-[10px] text-slate-400 font-mono">{txn.reference.slice(0, 8)}</p>}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}

function ActionButton({ icon: Icon, label, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group rounded-2xl bg-white/10 hover:bg-white/20 backdrop-blur border border-white/10 py-2.5 px-2 text-white font-semibold text-sm transition focus-visible:ring-4 focus-visible:ring-mtn-yellow/30 focus:outline-none"
    >
      <span className="flex flex-col items-center gap-1">
        <Icon className="w-4 h-4 text-mtn-yellow" aria-hidden="true" />
        <span className="text-[11px] tracking-wide">{label}</span>
      </span>
    </button>
  )
}

function Modal({ title, subtitle, children, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in" role="dialog" aria-modal="true">
      <div className="relative w-full max-w-md bg-white rounded-3xl p-5 shadow-lift animate-slide-up max-h-[90vh] overflow-y-auto">
        <button type="button" onClick={onClose} className="absolute top-4 right-4 w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 hover:bg-slate-100 focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none" aria-label="Close">
          <X className="w-4 h-4" />
        </button>
        <h3 className="font-display text-xl font-bold text-mtn-dark mb-1">{title}</h3>
        {subtitle && <p className="text-sm text-slate-500 mb-4">{subtitle}</p>}
        {children}
      </div>
    </div>
  )
}

function ErrorBox({ message }) {
  return (
    <div className="flex items-start gap-2 px-3 py-2.5 rounded-xl bg-red-50 border border-red-100" role="alert" aria-live="assertive">
      <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" aria-hidden="true" />
      <p className="text-sm text-red-700">{message}</p>
    </div>
  )
}

function Form({ onSubmit, busy, error, amount, setAmount, phone, setPhone, phoneLabel = 'Phone number', note, setNote, submitLabel, submitIcon: SubmitIcon }) {
  return (
    <form onSubmit={onSubmit} className="space-y-3" aria-label="Wallet action">
      <div>
        <label htmlFor="amt" className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">Amount (ZAR)</label>
        <input id="amt" type="number" inputMode="decimal" min="1" step="0.01" required value={amount} onChange={(e) => setAmount(e.target.value)} className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:border-mtn-blue focus:ring-4 focus:ring-mtn-blue/10 outline-none transition" />
      </div>
      <div>
        <label htmlFor="phn" className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">{phoneLabel}</label>
        <input id="phn" type="tel" inputMode="tel" placeholder="e.g. 083 123 4567" value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:border-mtn-blue focus:ring-4 focus:ring-mtn-blue/10 outline-none transition" />
      </div>
      <div>
        <label htmlFor="nt" className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wider">Note (optional)</label>
        <input id="nt" type="text" value={note} onChange={(e) => setNote(e.target.value)} className="w-full px-4 py-3 rounded-2xl bg-slate-50 border border-slate-200 text-sm focus:bg-white focus:border-mtn-blue focus:ring-4 focus:ring-mtn-blue/10 outline-none transition" />
      </div>
      {error && <ErrorBox message={error} />}
      <SubmitRow busy={busy} onCancel={() => {}} label={submitLabel} icon={SubmitIcon} />
    </form>
  )
}

function SubmitRow({ busy, onCancel, label, icon: Icon }) {
  return (
    <div className="flex gap-2 mt-5">
      <button type="submit" disabled={busy} className="flex-1 inline-flex items-center justify-center gap-2 bg-gradient-to-r from-mtn-yellow to-mtn-yellow-deep text-mtn-blue-deep font-bold py-3 rounded-2xl shadow-glow-yellow hover:shadow-lift disabled:opacity-60 focus-visible:ring-4 focus-visible:ring-mtn-blue/30 focus:outline-none transition">
        {Icon && <Icon className="w-4 h-4" aria-hidden="true" />}
        {busy ? t_b('auth.please_wait') : label}
      </button>
    </div>
  )
}

function t_b(k) { return k === 'auth.please_wait' ? 'Working…' : k }