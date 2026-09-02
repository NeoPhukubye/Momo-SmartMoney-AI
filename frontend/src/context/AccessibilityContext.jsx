import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AccessibilityContext = createContext(null);

const DEFAULTS = {
  fontSize: 'medium',
  highContrast: false,
  reducedMotion: false,
  screenReader: false,
  dyslexiaFont: false,
  darkMode: false,
  voiceEnabled: false,
};

export function AccessibilityProvider({ children }) {
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('a11y_settings');
    if (saved) {
      try { return { ...DEFAULTS, ...JSON.parse(saved) }; } catch { /* ignore */ }
    }
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return { ...DEFAULTS, reducedMotion: prefersReduced, darkMode: prefersDark };
  });

  useEffect(() => {
    localStorage.setItem('a11y_settings', JSON.stringify(settings));
  }, [settings]);

  useEffect(() => {
    const root = document.documentElement;
    const classes = [];

    if (settings.highContrast) classes.push('high-contrast');
    if (settings.reducedMotion) classes.push('reduce-motion');
    if (settings.dyslexiaFont) classes.push('dyslexia-font');
    if (settings.darkMode) classes.push('dark-mode');
    classes.push(`font-size-${settings.fontSize}`);
    if (settings.screenReader) classes.push('sr-enhanced');

    root.className = classes.join(' ');

    if (settings.reducedMotion) {
      root.style.setProperty('--animation-duration', '0s');
      root.style.setProperty('--transition-duration', '0s');
    } else {
      root.style.removeProperty('--animation-duration');
      root.style.removeProperty('--transition-duration');
    }
  }, [settings]);

  const updateSetting = useCallback((key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  const toggleSetting = useCallback((key) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULTS);
  }, []);

  const announce = useCallback((message, priority = 'polite') => {
    const el = document.getElementById(`a11y-announcer-${priority}`);
    if (el) {
      el.textContent = '';
      setTimeout(() => { el.textContent = message; }, 50);
    }
  }, []);

  return (
    <AccessibilityContext.Provider value={{ settings, updateSetting, toggleSetting, resetSettings, announce }}>
      <div id="a11y-announcer-polite" aria-live="polite" aria-atomic="true" className="sr-only" />
      <div id="a11y-announcer-assertive" aria-live="assertive" aria-atomic="true" className="sr-only" />
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (!context) throw new Error('useAccessibility must be used within AccessibilityProvider');
  return context;
}
