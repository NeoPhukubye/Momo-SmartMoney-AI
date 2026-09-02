import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, Zap, Mic, MicOff } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../context/AccessibilityContext'
import api from '../services/api'

export default function Chat() {
  const { t } = useTranslation()
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
      const { data } = await api.post('/api/coaching/chat', { message: userMsg })
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

  const getCategoryColor = (category) => {
    const colors = {
      spending: 'bg-orange-50 border-orange-200',
      savings: 'bg-green-50 border-green-200',
      security: 'bg-red-50 border-red-200',
      stokvel: 'bg-purple-50 border-purple-200',
    }
    return colors[category] || 'bg-white border-gray-100'
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)]" role="region" aria-label={t('chat.title')}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-3 pb-3 border-b border-gray-100">
        <div className="w-10 h-10 rounded-full gradient-mtn flex items-center justify-center animate-pulse-glow" aria-hidden="true">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h2 className="text-lg font-bold text-mtn-dark leading-tight">{t('chat.title')}</h2>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 bg-green-400 rounded-full" aria-hidden="true" />
            <p className="text-xs text-gray-500">{t('chat.powered_by')}</p>
          </div>
        </div>
        <div className="flex items-center gap-1 bg-mtn-yellow/20 px-2 py-1 rounded-full" aria-hidden="true">
          <Zap className="w-3 h-3 text-mtn-blue" />
          <span className="text-[10px] font-bold text-mtn-blue">AI</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 pb-4" role="log" aria-live="polite" aria-label="Chat messages">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 animate-slide-up ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-mtn-yellow flex items-center justify-center flex-shrink-0 mt-1" aria-hidden="true">
                <Bot className="w-4 h-4 text-mtn-blue" />
              </div>
            )}
            <div className="max-w-[80%]">
              <div
                className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-mtn-blue text-white rounded-br-sm'
                    : `${getCategoryColor(msg.category)} border rounded-bl-sm`
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
                      className="text-xs bg-mtn-yellow/20 text-mtn-blue px-3 py-1.5 rounded-full hover:bg-mtn-yellow/40 transition border border-mtn-yellow/30 disabled:opacity-50 card-hover focus-visible:ring-2 focus-visible:ring-mtn-yellow focus:outline-none"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
              <p className="text-[10px] text-gray-300 mt-1 px-1" aria-hidden="true">
                {msg.time?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-mtn-blue flex items-center justify-center flex-shrink-0 mt-1" aria-hidden="true">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-2 animate-slide-up" role="status" aria-label={t('chat.analyzing')}>
            <div className="w-7 h-7 rounded-full bg-mtn-yellow flex items-center justify-center" aria-hidden="true">
              <Bot className="w-4 h-4 text-mtn-blue" />
            </div>
            <div className="bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-100">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5" aria-hidden="true">
                  <span className="w-2 h-2 bg-mtn-blue/40 rounded-full animate-bounce-1" />
                  <span className="w-2 h-2 bg-mtn-blue/40 rounded-full animate-bounce-2" />
                  <span className="w-2 h-2 bg-mtn-blue/40 rounded-full animate-bounce-3" />
                </div>
                <span className="text-xs text-gray-400 ml-1">{t('chat.analyzing')}</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEnd} />
      </div>

      {/* Input */}
      <div className="flex gap-2 pt-3 border-t border-gray-100">
        <button
          onClick={toggleVoiceInput}
          className={`w-10 h-10 rounded-full flex items-center justify-center transition shadow-sm ${
            isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
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
          className="flex-1 px-4 py-2.5 rounded-full border border-gray-200 focus:ring-2 focus:ring-mtn-yellow focus:border-transparent outline-none text-sm disabled:opacity-50 transition"
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || loading}
          aria-label={t('common.send')}
          className="w-10 h-10 bg-mtn-yellow rounded-full flex items-center justify-center disabled:opacity-40 hover:bg-yellow-400 transition shadow-sm active:scale-95 focus-visible:ring-2 focus-visible:ring-mtn-blue focus:outline-none"
        >
          <Send className="w-4 h-4 text-mtn-blue" aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}
