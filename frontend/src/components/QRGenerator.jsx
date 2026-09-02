import { useEffect, useRef, useState } from 'react'
import QRCode from 'qrcode'
import { Download } from 'lucide-react'

/**
 * Renders a QR code for the given payload, with an optional "Download PNG" affordance.
 * Uses the `qrcode` library to draw to a <canvas>.
 */
export default function QRGenerator({ payload, size = 220, label, className = '' }) {
  const canvasRef = useRef(null)
  const [dataUrl, setDataUrl] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (!payload || !canvasRef.current) return
    QRCode.toCanvas(canvasRef.current, payload, {
      width: size,
      margin: 1,
      errorCorrectionLevel: 'M',
      color: { dark: '#003087', light: '#FFFFFF' },
    }).catch((err) => setError(err.message || 'Could not render QR'))
    QRCode.toDataURL(payload, {
      width: size * 2,
      margin: 1,
      errorCorrectionLevel: 'M',
      color: { dark: '#003087', light: '#FFFFFF' },
    })
      .then(setDataUrl)
      .catch(() => {})
  }, [payload, size])

  const handleDownload = () => {
    if (!dataUrl) return
    const link = document.createElement('a')
    link.href = dataUrl
    link.download = `smartmoney-qr-${(payload || 'code').replace(/[^a-z0-9]+/gi, '-').slice(0, 24)}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className={`flex flex-col items-center gap-2 ${className}`}>
      <div className="rounded-2xl bg-white p-3 shadow-soft border border-slate-200">
        <canvas ref={canvasRef} aria-label={label || 'QR code'} role="img" />
      </div>
      {label && <p className="text-xs font-semibold text-slate-600 text-center break-all">{label}</p>}
      {error && <p className="text-xs text-red-600" role="alert">{error}</p>}
      {dataUrl && (
        <button
          type="button"
          onClick={handleDownload}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-mtn-blue hover:text-mtn-blue-light focus-visible:underline focus:outline-none rounded px-2 py-1"
        >
          <Download className="w-3.5 h-3.5" aria-hidden="true" />
          Download PNG
        </button>
      )}
    </div>
  )
}