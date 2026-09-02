import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { AccessibilityProvider } from './context/AccessibilityContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Stokvel from './pages/Stokvel'
import Transactions from './pages/Transactions'
import Login from './pages/Login'
import './i18n'

function App() {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const storedUser = localStorage.getItem('user')
    if (storedUser && token) {
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [token])

  const handleLogin = (userData, accessToken) => {
    setUser(userData)
    setToken(accessToken)
    localStorage.setItem('token', accessToken)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const handleLogout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-mtn-yellow flex items-center justify-center" role="status" aria-label="Loading application">
        <div className="text-center">
          <div className="w-16 h-16 bg-mtn-blue rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
            <span className="text-2xl text-white font-bold" aria-hidden="true">S</span>
          </div>
          <p className="text-mtn-blue font-semibold">SmartMoney AI</p>
        </div>
      </div>
    )
  }

  if (!token) {
    return (
      <AccessibilityProvider>
        <Login onLogin={handleLogin} />
      </AccessibilityProvider>
    )
  }

  return (
    <AccessibilityProvider>
      <BrowserRouter>
        <Layout user={user} onLogout={handleLogout}>
          <div className="page-transition">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/stokvel" element={<Stokvel />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </div>
        </Layout>
      </BrowserRouter>
    </AccessibilityProvider>
  )
}

export default App
