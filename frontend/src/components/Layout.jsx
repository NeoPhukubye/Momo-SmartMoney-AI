import { NavLink } from 'react-router-dom';
import { Home, MessageCircle, Users, List, LogOut, Shield, Accessibility } from 'lucide-react';
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
    { to: '/transactions', icon: List, label: t('common.transactions') },
  ];

  const bgClass = settings.highContrast
    ? 'bg-black text-white'
    : settings.darkMode
    ? 'bg-gray-900 text-white'
    : 'bg-mtn-light text-gray-900';

  const headerClass = settings.highContrast
    ? 'bg-yellow-400 text-black'
    : 'bg-mtn-yellow';

  const navBgClass = settings.highContrast
    ? 'bg-black border-yellow-400'
    : settings.darkMode
    ? 'bg-gray-900 border-gray-700'
    : 'bg-white border-gray-200';

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
      <header className={`${headerClass} px-4 py-3 flex items-center justify-between shadow-sm`} role="banner">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-mtn-blue" aria-hidden="true" />
          <h1 className="text-lg font-bold text-mtn-blue">SmartMoney AI</h1>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setA11yOpen(true)}
            aria-label={t('a11y.accessibility_settings')}
            className="p-2 rounded-full hover:bg-white/20 text-mtn-blue transition"
          >
            <Accessibility className="w-5 h-5" aria-hidden="true" />
          </button>
          <LanguageSwitcher />
          <span className="text-sm text-mtn-dark font-medium hidden sm:inline" aria-label={`User: ${user?.name}`}>
            {user?.name}
          </span>
          <button
            onClick={onLogout}
            className="text-mtn-blue hover:text-red-600 p-2 transition"
            aria-label={t('common.logout')}
          >
            <LogOut className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main
        id="main-content"
        className="flex-1 p-4 pb-20 max-w-md mx-auto w-full"
        role="main"
        aria-label={t('a11y.main_content')}
        tabIndex={-1}
      >
        {children}
      </main>

      {/* Bottom Navigation */}
      <nav
        id="bottom-nav"
        className={`fixed bottom-0 left-0 right-0 ${navBgClass} border-t px-4 py-2 safe-bottom`}
        role="navigation"
        aria-label={t('a11y.navigation')}
      >
        <div className="max-w-md mx-auto flex justify-around">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 text-xs transition-colors py-1 px-2 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-mtn-yellow ${
                  isActive
                    ? settings.highContrast
                      ? 'text-yellow-400 font-bold'
                      : 'text-mtn-blue font-bold'
                    : settings.highContrast
                    ? 'text-white'
                    : settings.darkMode
                    ? 'text-gray-400'
                    : 'text-gray-500'
                }`
              }
              aria-label={label}
            >
              {({ isActive }) => (
                <>
                  <Icon className="w-5 h-5" aria-hidden="true" />
                  <span aria-hidden="true">{label}</span>
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
