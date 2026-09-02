import { useCallback, useEffect, useRef, useState } from 'react'
import jsQR from 'jsqr'
import { Camera, Upload, X, RefreshCw, ScanLine } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import api from '../services/api'
import { useAccessibility } from '../context/AccessibilityContext'

/**
 * Camera-first QR scanner with a file-upload fallback (useful on desktop
 * and when camera permission is denied). Calls /api/wallet/scan server-side
 * to normalise the raw string into a typed payload.
 */
export default function QRScanner({ onResult, onClose }) {
  const { t } = useTranslation()
  const { announce } = useAccessibility()
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const fileRef = useRef(null)
  const streamRef = useRef(null)
  const rafRef = useRef(0)
  const stopRef = useRef(false)

  const [cameraState, setCameraState] = useState('idle') // idle | starting | running | error
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const stopAll = useCallback(() => {
    stopRef.current = true
    cancelAnimationFrame(rafRef.current)
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) videoRef.current.srcObject = null
  }, [])

  useEffect(() => () => stopAll(), [stopAll])

  const startCamera = useCallback(async () => {
    setError('')
    setCameraState('starting')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setCameraState('running')
      stopRef.current = false
      announce('Camera started')

      const tick = () => {
        if (stopRef.current) return
        const video = videoRef.current
        const canvas = canvasRef.current
        if (video && canvas && video.readyState >= 2) {
          const w = video.videoWidth
          const h = video.videoHeight
          if (w && h) {
            canvas.width = w
            canvas.height = h
            const ctx = canvas.getContext('2d', { willReadFrequently: true })
            ctx.drawImage(video, 0, 0, w, h)
            const imageData = ctx.getImageData(0, 0, w, h)
            const code = jsQR(imageData.data, w, h, { inversionAttempts: 'dontInvert' })
            if (code && code.data) {
              handleRaw(code.data)
              return
            }
          }
        }
        rafRef.current = requestAnimationFrame(tick)
      }
      rafRef.current = requestAnimationFrame(tick)
    } catch (err) {
      setCameraState('error')
      setError(err?.message || 'Could not access camera. Use the upload option below.')
      announce('Camera unavailable', 'assertive')
    }
  }, [announce]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleRaw = useCallback(
    async (raw) => {
      setBusy(true)
      stopAll()
      try {
        const { data } = await api.post('/api/wallet/scan', { raw })
        announce('QR scanned')
        onResult?.(data, raw)
      } catch (err) {
        setError('Could not interpret scan. Please try again.')
        announce('Scan failed', 'assertive')
      } finally {
        setBusy(false)
      }
    },
    [onResult, stopAll, announce]
  )

  const onFile = useCallback(
    async (event) => {
      const file = event.target.files?.[0]
      if (!file) return
      setBusy(true)
      setError('')
      try {
        const img = await loadImage(file)
        const canvas = canvasRef.current
        canvas.width = img.naturalWidth
        canvas.height = img.naturalHeight
        const ctx = canvas.getContext('2d', { willReadFrequently: true })
        ctx.drawImage(img, 0, 0)
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const code = jsQR(imageData.data, canvas.width, canvas.height, { inversionAttempts: 'attemptBoth' })
        if (!code || !code.data) {
          setError('No QR code found in that image.')
        } else {
          await handleRaw(code.data)
        }
      } catch (err) {
        setError('Could not read that image.')
      } finally {
        setBusy(false)
        if (fileRef.current) fileRef.current.value = ''
      }
    },
    [handleRaw]
  )

  return (
    <div className="space-y-3" role="region" aria-label="QR scanner">
      <div className="relative overflow-hidden rounded-2xl bg-slate-900 aspect-[4/3]">
        <video
          ref={videoRef}
          playsInline
          muted
          className="w-full h-full object-cover"
          aria-label="Camera preview"
        />
        <canvas ref={canvasRef} className="hidden" aria-hidden="true" />

        {/* Overlay frame */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute inset-8 border-2 border-mtn-yellow/80 rounded-2xl shadow-[0_0_0_9999px_rgba(0,0,0,0.45)]" />
          <div className="absolute inset-x-8 top-1/2 h-0.5 bg-mtn-yellow/80 animate-pulse" />
        </div>

        {cameraState === 'idle' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-white gap-2 p-4 text-center">
            <ScanLine className="w-10 h-10 text-mtn-yellow" aria-hidden="true" />
            <p className="text-sm font-medium">Camera off</p>
            <button
              type="button"
              onClick={startCamera}
              className="mt-1 inline-flex items-center gap-1.5 bg-mtn-yellow text-mtn-blue-deep font-semibold text-sm px-4 py-2 rounded-xl focus-visible:ring-2 focus-visible:ring-white focus:outline-none"
            >
              <Camera className="w-4 h-4" aria-hidden="true" />
              Start camera
            </button>
          </div>
        )}

        {cameraState === 'starting' && (
          <div className="absolute inset-0 flex items-center justify-center text-white text-sm">
            <span className="inline-block w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" aria-hidden="true" />
            Starting camera…
          </div>
        )}

        {cameraState === 'error' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-white gap-1.5 p-4 text-center">
            <p className="text-sm font-medium">Camera unavailable</p>
            <p className="text-xs text-white/70">Use the upload option below.</p>
          </div>
        )}

        {busy && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40 text-white text-sm">
            <span className="inline-block w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" aria-hidden="true" />
            Reading QR…
          </div>
        )}

        {cameraState === 'running' && (
          <button
            type="button"
            onClick={() => { stopAll(); setCameraState('idle') }}
            className="absolute top-2 right-2 w-9 h-9 rounded-full bg-black/50 text-white flex items-center justify-center backdrop-blur focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
            aria-label="Stop camera"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600" role="alert" aria-live="assertive">{error}</p>
      )}

      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => { stopAll(); setCameraState('idle'); fileRef.current?.click() }}
          className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white border border-slate-200 text-slate-700 text-sm font-semibold py-2.5 hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
        >
          <Upload className="w-4 h-4" aria-hidden="true" />
          Upload image
        </button>
        <button
          type="button"
          onClick={async () => { stopAll(); setCameraState('idle'); await startCamera() }}
          className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-900 text-white text-sm font-semibold py-2.5 hover:bg-slate-800 focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
        >
          <RefreshCw className="w-4 h-4" aria-hidden="true" />
          {cameraState === 'running' ? 'Restart camera' : 'Retry camera'}
        </button>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={onFile}
        className="sr-only"
        aria-label="Upload a QR code image"
      />

      {onClose && (
        <button
          type="button"
          onClick={() => { stopAll(); onClose() }}
          className="w-full text-sm text-slate-500 hover:text-slate-700 focus-visible:underline focus:outline-none rounded px-2 py-1.5"
        >
          {t('common.cancel')}
        </button>
      )}
    </div>
  )
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = reject
      img.src = reader.result
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}