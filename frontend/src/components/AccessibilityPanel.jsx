import { useTranslation } from 'react-i18next';
import { useAccessibility } from '../context/AccessibilityContext';
import { Eye, Type, Moon, Sun, Volume2, Zap, RotateCcw, X } from 'lucide-react';

export default function AccessibilityPanel({ isOpen, onClose }) {
  const { t } = useTranslation();
  const { settings, updateSetting, toggleSetting, resetSettings } = useAccessibility();

  if (!isOpen) return null;

  const fontSizes = [
    { value: 'small', label: t('a11y.small') },
    { value: 'medium', label: t('a11y.medium') },
    { value: 'large', label: t('a11y.large') },
    { value: 'extra_large', label: t('a11y.extra_large') },
  ];

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label={t('a11y.accessibility_settings')}
    >
      <div className="absolute inset-0 bg-black/50" onClick={onClose} aria-hidden="true" />
      <div className="relative bg-white dark:bg-gray-900 rounded-t-2xl sm:rounded-2xl w-full max-w-md max-h-[85vh] overflow-y-auto p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold" id="a11y-panel-title">
            {t('a11y.accessibility_settings')}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label={t('common.close')}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-5">
          {/* Font Size */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium mb-2">
              <Type className="w-4 h-4" aria-hidden="true" />
              {t('a11y.font_size')}
            </label>
            <div className="grid grid-cols-4 gap-2" role="radiogroup" aria-label={t('a11y.font_size')}>
              {fontSizes.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => updateSetting('fontSize', value)}
                  role="radio"
                  aria-checked={settings.fontSize === value}
                  className={`py-2 px-3 rounded-lg text-xs font-medium border transition-all ${
                    settings.fontSize === value
                      ? 'bg-mtn-yellow text-mtn-blue border-mtn-yellow'
                      : 'bg-gray-50 border-gray-200 hover:border-mtn-yellow'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Toggle Controls */}
          <ToggleRow
            icon={<Eye className="w-4 h-4" />}
            label={t('a11y.high_contrast')}
            checked={settings.highContrast}
            onChange={() => toggleSetting('highContrast')}
          />
          <ToggleRow
            icon={settings.darkMode ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            label={settings.darkMode ? t('a11y.dark_mode') : t('a11y.light_mode')}
            checked={settings.darkMode}
            onChange={() => toggleSetting('darkMode')}
          />
          <ToggleRow
            icon={<Zap className="w-4 h-4" />}
            label={t('a11y.reduce_motion')}
            checked={settings.reducedMotion}
            onChange={() => toggleSetting('reducedMotion')}
          />
          <ToggleRow
            icon={<Type className="w-4 h-4" />}
            label={t('a11y.dyslexia_font')}
            checked={settings.dyslexiaFont}
            onChange={() => toggleSetting('dyslexiaFont')}
          />
          <ToggleRow
            icon={<Volume2 className="w-4 h-4" />}
            label={t('a11y.screen_reader_friendly')}
            checked={settings.screenReader}
            onChange={() => toggleSetting('screenReader')}
          />

          {/* Reset */}
          <button
            onClick={resetSettings}
            className="flex items-center gap-2 w-full justify-center py-3 text-sm text-gray-500 hover:text-red-500 border border-gray-200 rounded-lg transition"
          >
            <RotateCcw className="w-4 h-4" />
            Reset to defaults
          </button>
        </div>
      </div>
    </div>
  );
}

function ToggleRow({ icon, label, checked, onChange }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="flex items-center gap-2 text-sm font-medium">
        <span aria-hidden="true">{icon}</span>
        {label}
      </span>
      <button
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={onChange}
        className={`relative w-11 h-6 rounded-full transition-colors ${
          checked ? 'bg-mtn-blue' : 'bg-gray-300'
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}
