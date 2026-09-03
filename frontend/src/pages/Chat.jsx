import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, Zap, Mic, MicOff } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import api from '../services/api'

export default function Chat() {
  const { t, i18n } = useTranslation()
  const { announce, settings } = useAccessibility()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: t('chat.greeting'),
      suggestions: [t('chat.suggestion_month'), t('chat.suggestion_save'), t('chat.suggestion_scam')],
      time: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const messagesEnd = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: settings.reducedMotion ? 'auto' : 'smooth' })
  }, [messages, settings.reducedMotion])

  const sendMessage = async (text) => {
    const userMsg = text || input
    if (!userMsg.trim() || loading) return

    setMessages((prev) => [...prev, { role: 'user', content: userMsg, time: new Date() }])
    setInput('')
    setLoading(true)
    announce(t('chat.analyzing'))

    try {
      const { data } = await api.post('/api/coaching/chat', {
        message: userMsg,
        language: i18n.language || 'en',
      })
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response,
          suggestions: data.suggestions,
          category: data.category,
          time: new Date(),
        },
      ])
      announce(data.response)
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: t('chat.error_message'),
          time: new Date(),
        },
      ])
      announce(t('a11y.error_occurred'), 'assertive')
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const toggleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      announce('Voice input not supported in this browser', 'assertive')
      return
    }

    if (isListening) {
      setIsListening(false)
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onstart = () => {
      setIsListening(true)
      announce(t('chat.voice_listening'))
    }
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setInput(transcript)
      setIsListening(false)
    }
    recognition.onerror = () => setIsListening(false)
    recognition.onend = () => setIsListening(false)
    recognition.start()
  }

  const getCategoryStyle = (category) => {
    const styles = {
      spending: 'from-orange-50 to-amber-50 border-orange-100 text-slate-800',
      savings: 'from-emerald-50 to-green-50 border-emerald-100 text-slate-800',
      security: 'from-rose-50 to-red-50 border-rose-100 text-slate-800',
      stokvel: 'from-violet-50 to-purple-50 border-violet-100 text-slate-800',
    }
    return styles[category] || 'from-white to-slate-50 border-slate-100 text-slate-800'
  }

  return (
    <div className="flex flex-col h-[calc(100vh-160px)] animate-fade-in" role="region" aria-label={t('chat.title')}>
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl mb-3 px-4 py-3.5 bg-gradient-to-br from-mtn-blue to-mtn-blue-deep text-white shadow-glow-blue">
        <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-mtn-yellow/20 blur-2xl pointer-events-none" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <div className="relative w-11 h-11 rounded-2xl bg-white/15 backdrop-blur flex items-center justify-center animate-pulse-soft" aria-hidden="true">
            <Sparkles className="w-5 h-5 text-mtn-yellow" />
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 ring-2 ring-mtn-blue-deep" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="font-display font-bold text-lg leading-tight">{t('chat.title')}</h2>
            <p className="text-[11px] text-white/70 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
              {t('chat.powered_by')}
            </p>
          </div>
          <div className="flex items-center gap-1 bg-mtn-yellow/20 backdrop-blur px-2.5 py-1 rounded-full border border-mtn-yellow/30" aria-hidden="true">
            <Zap className="w-3 h-3 text-mtn-yellow" />
            <span className="text-[10px] font-extrabold text-mtn-yellow tracking-wider">AI</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 pb-3 px-1 -mx-1" role="log" aria-live="polite" aria-label="Chat messages">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 animate-slide-up ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-2xl bg-gradient-to-br from-mtn-yellow to-mtn-yellow-deep flex items-center justify-center flex-shrink-0 mt-1 shadow-soft" aria-hidden="true">
                <Bot className="w-4 h-4 text-mtn-blue-deep" />
              </div>
            )}
            <div className="max-w-[80%]">
              <div
                className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-soft ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-br from-mtn-blue to-mtn-blue-deep text-white rounded-br-md'
                    : `bg-gradient-to-br ${getCategoryStyle(msg.category)} border rounded-bl-md`
                }`}
                role={msg.role === 'assistant' ? 'status' : undefined}
              >
                {msg.content}
              </div>
              {msg.suggestions?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2" role="group" aria-label="Suggested responses">
                  {msg.suggestions.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(s)}
                      disabled={loading}
                      className="text-xs bg-white text-mtn-blue px-3 py-1.5 rounded-full hover:bg-mtn-yellow border border-mtn-yellow/40 transition disabled:opacity-50 card-hover font-medium focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
              <p className="text-[10px] text-slate-400 mt-1 px-1" aria-hidden="true">
                {msg.time?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center flex-shrink-0 mt-1 shadow-soft" aria-hidden="true">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-2 animate-slide-up" role="status" aria-label={t('chat.analyzing')}>
            <div className="w-8 h-8 rounded-2xl bg-gradient-to-br from-mtn-yellow to-mtn-yellow-deep flex items-center justify-center" aria-hidden="true">
              <Bot className="w-4 h-4 text-mtn-blue-deep" />
            </div>
            <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 shadow-soft border border-slate-100">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5" aria-hidden="true">
                  <span className="w-2 h-2 bg-mtn-blue rounded-full animate-bounce-1" />
                  <span className="w-2 h-2 bg-mtn-blue rounded-full animate-bounce-2" />
                  <span className="w-2 h-2 bg-mtn-blue rounded-full animate-bounce-3" />
                </div>
                <span className="text-xs text-slate-500 font-medium">{t('chat.analyzing')}</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEnd} />
      </div>

      {/* Input */}
      <div className="flex gap-2 pt-3 mt-1 border-t border-slate-200/70">
        <button
          onClick={toggleVoiceInput}
          className={`relative w-11 h-11 rounded-2xl flex items-center justify-center transition shadow-soft focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none ${
            isListening
              ? 'bg-gradient-to-br from-red-500 to-rose-600 text-white animate-pulse'
              : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
          }`}
          aria-label={isListening ? t('chat.voice_listening') : t('chat.voice_input')}
          aria-pressed={isListening}
        >
          {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder={t('chat.placeholder')}
          disabled={loading}
          aria-label={t('chat.placeholder')}
          className="flex-1 px-4 py-2.5 rounded-2xl border border-slate-200 bg-white focus:ring-4 focus:ring-mtn-blue/10 focus:border-mtn-blue outline-none text-sm disabled:opacity-50 transition placeholder:text-slate-400"
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          aria-label={t('common.send')}
          className="group relative w-11 h-11 rounded-2xl bg-gradient-to-br from-mtn-yellow to-mtn-yellow-deep flex items-center justify-center disabled:opacity-40 hover:shadow-glow-yellow transition shadow-soft active:scale-95 focus-visible:ring-4 focus-visible:ring-mtn-blue/30 focus:outline-none"
        >
          <Send className="w-4 h-4 text-mtn-blue-deep transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}