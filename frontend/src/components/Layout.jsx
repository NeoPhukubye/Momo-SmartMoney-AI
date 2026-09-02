import { NavLink } from 'react-router-dom';
import { Home, MessageCircle, Users, List, Wallet, LogOut, Shield, Accessibility } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import LanguageSwitcher from './LanguageSwitcher';
import AccessibilityPanel from './AccessibilityPanel';
import { useAccessibility } from '../context/AccessibilityContext';

export default function Layout({ user, onLogout, children }) {
  const { t } = useTranslation();
  const { settings } = useAccessibility();
  const [a11yOpen, setA11yOpen] = useState(false);

  const navItems = [
    { to: '/', icon: Home, label: t('common.dashboard') },
    { to: '/chat', icon: MessageCircle, label: t('common.chat') },
    { to: '/stokvel', icon: Users, label: t('common.stokvel') },
    { to: '/wallet', icon: Wallet, label: t('common.wallet') || 'Wallet' },
    { to: '/transactions', icon: List, label: t('common.transactions') },
  ];

  const bgClass = settings.highContrast
    ? 'bg-black text-white'
    : settings.darkMode
    ? 'bg-mesh-dark text-white'
    : 'bg-mesh-light text-slate-900';

  const headerBg = settings.highContrast
    ? 'bg-yellow-400 text-black border-yellow-400'
    : 'glass border-white/40';

  const navBg = settings.highContrast
    ? 'bg-black border-yellow-400'
    : settings.darkMode
    ? 'glass-dark border-white/10'
    : 'glass border-white/50';

  return (
    <div className={`min-h-screen flex flex-col ${bgClass}`}>
      {/* Skip Navigation - Critical for screen readers */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[200] focus:bg-mtn-yellow focus:text-mtn-blue focus:px-4 focus:py-2 focus:rounded-lg focus:font-bold focus:shadow-lg"
      >
        {t('a11y.skip_to_content')}
      </a>
      <a
        href="#bottom-nav"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-44 focus:z-[200] focus:bg-mtn-yellow focus:text-mtn-blue focus:px-4 focus:py-2 focus:rounded-lg focus:font-bold focus:shadow-lg"
      >
        {t('a11y.skip_to_nav')}
      </a>

      {/* Header */}
      <header
        className={`sticky top-0 z-30 ${headerBg} px-4 py-3 flex items-center justify-between border-b`}
        role="banner"
      >
        <div className="flex items-center gap-2.5">
          <div className="relative w-9 h-9 rounded-2xl bg-gradient-to-br from-mtn-yellow to-mtn-yellow-deep flex items-center justify-center shadow-glow-yellow">
            <Shield className="w-4 h-4 text-mtn-blue-deep" aria-hidden="true" />
          </div>
          <div className="leading-tight">
            <h1 className="font-display font-extrabold text-mtn-blue text-base tracking-tight">SmartMoney</h1>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-mtn-blue/70">AI Coach</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setA11yOpen(true)}
            aria-label={t('a11y.accessibility_settings')}
            className="p-2 rounded-xl hover:bg-white/30 text-mtn-blue transition focus-visible:ring-2 focus-visible:ring-mtn-blue focus:outline-none"
          >
            <Accessibility className="w-5 h-5" aria-hidden="true" />
          </button>
          <LanguageSwitcher />
          <span
            className="hidden sm:inline-flex items-center px-3 py-1 rounded-full bg-mtn-yellow/20 text-mtn-blue text-xs font-semibold border border-mtn-yellow/30"
            aria-label={`User: ${user?.name}`}
          >
            {user?.name}
          </span>
          <button
            onClick={onLogout}
            className="p-2 rounded-xl hover:bg-red-50 text-mtn-blue hover:text-red-600 transition focus-visible:ring-2 focus-visible:ring-red-500 focus:outline-none"
            aria-label={t('common.logout')}
          >
            <LogOut className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main
        id="main-content"
        className="flex-1 p-4 pb-28 max-w-md mx-auto w-full"
        role="main"
        aria-label={t('a11y.main_content')}
        tabIndex={-1}
      >
        {children}
      </main>

      {/* Floating Bottom Navigation */}
      <nav
        id="bottom-nav"
        className={`fixed bottom-4 left-1/2 -translate-x-1/2 z-40 ${navBg} rounded-3xl px-2 py-2 shadow-lift max-w-[calc(100%-2rem)]`}
        role="navigation"
        aria-label={t('a11y.navigation')}
      >
        <div className="flex justify-around items-center gap-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `relative flex flex-col items-center gap-0.5 text-[10px] transition-all py-1.5 px-3 rounded-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-mtn-yellow ${
                  isActive
                    ? settings.highContrast
                      ? 'text-yellow-400 font-bold bg-yellow-400/10'
                      : 'text-mtn-blue-deep font-bold bg-gradient-to-br from-mtn-yellow to-mtn-yellow-deep shadow-glow-yellow'
                    : settings.highContrast
                    ? 'text-white'
                    : settings.darkMode
                    ? 'text-slate-400 hover:text-white'
                    : 'text-slate-500 hover:text-mtn-blue'
                }`
              }
              aria-label={label}
            >
              {({ isActive }) => (
                <>
                  <Icon className={`w-4 h-4 transition-transform ${isActive ? 'scale-110' : ''}`} aria-hidden="true" />
                  <span className="font-semibold tracking-wide">{label}</span>
                  {isActive && <span className="sr-only">({t('a11y.current_page')})</span>}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Accessibility Panel */}
      <AccessibilityPanel isOpen={a11yOpen} onClose={() => setA11yOpen(false)} />
    </div>
  );
}