import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Search, X } from 'lucide-react';

const languages = [
  { code: 'en', name: 'English', native: 'English', region: 'global' },
  { code: 'af', name: 'Afrikaans', native: 'Afrikaans', region: 'southern' },
  { code: 'zu', name: 'Zulu', native: 'isiZulu', region: 'southern' },
  { code: 'xh', name: 'Xhosa', native: 'isiXhosa', region: 'southern' },
  { code: 'st', name: 'Sesotho', native: 'Sesotho', region: 'southern' },
  { code: 'tn', name: 'Setswana', native: 'Setswana', region: 'southern' },
  { code: 'nso', name: 'Sepedi', native: 'Sepedi', region: 'southern' },
  { code: 'ts', name: 'Xitsonga', native: 'Xitsonga', region: 'southern' },
  { code: 've', name: 'Tshivenda', native: 'Tshivenḓa', region: 'southern' },
  { code: 'sw', name: 'Swahili', native: 'Kiswahili', region: 'east' },
  { code: 'am', name: 'Amharic', native: 'አማርኛ', region: 'east' },
  { code: 'ha', name: 'Hausa', native: 'Hausa', region: 'west' },
  { code: 'yo', name: 'Yoruba', native: 'Yorùbá', region: 'west' },
  { code: 'ig', name: 'Igbo', native: 'Igbo', region: 'west' },
  { code: 'fr', name: 'French', native: 'Français', region: 'global' },
  { code: 'pt', name: 'Portuguese', native: 'Português', region: 'global' },
];

const regionLabels = {
  southern: 'Southern Africa',
  east: 'East Africa',
  west: 'West Africa',
  global: 'International',
};

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const panelRef = useRef(null);
  const triggerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target) && !triggerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e) => { if (e.key === 'Escape') setIsOpen(false); };
    if (isOpen) document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  const filtered = languages.filter(l =>
    l.name.toLowerCase().includes(search.toLowerCase()) ||
    l.native.toLowerCase().includes(search.toLowerCase())
  );

  const grouped = {};
  filtered.forEach(l => {
    if (!grouped[l.region]) grouped[l.region] = [];
    grouped[l.region].push(l);
  });

  const currentLang = languages.find(l => i18n.language.startsWith(l.code));

  const selectLanguage = (code) => {
    i18n.changeLanguage(code);
    setIsOpen(false);
    setSearch('');
  };

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={t('a11y.switch_language')}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        className="flex items-center gap-1 text-mtn-blue p-2 rounded-full hover:bg-white/20 transition"
      >
        <Globe className="w-5 h-5" aria-hidden="true" />
        <span className="text-xs font-bold uppercase">{currentLang?.code || 'en'}</span>
      </button>

      {isOpen && (
        <div
          ref={panelRef}
          role="dialog"
          aria-label={t('a11y.switch_language')}
          className="absolute right-0 top-full mt-2 glass shadow-lift rounded-2xl overflow-hidden z-[90] w-72 max-h-[70vh] flex flex-col border border-white/40 animate-fade-in"
        >
          {/* Search */}
          <div className="p-3 border-b border-gray-100">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t('common.search') + '...'}
                className="w-full pl-9 pr-8 py-2 text-sm rounded-xl bg-white/70 border border-slate-200 focus:ring-2 focus:ring-mtn-yellow focus:border-mtn-yellow outline-none transition"
                aria-label={t('common.search')}
                autoFocus
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1"
                  aria-label={t('common.close')}
                >
                  <X className="w-3 h-3 text-gray-400" />
                </button>
              )}
            </div>
          </div>

          {/* Language List */}
          <div className="overflow-y-auto flex-1" role="listbox" aria-label={t('a11y.switch_language')}>
            {Object.entries(grouped).map(([region, langs]) => (
              <div key={region}>
                <div className="px-4 py-1.5 text-[10px] uppercase tracking-wider text-gray-400 font-semibold bg-gray-50">
                  {regionLabels[region]}
                </div>
                {langs.map((lang) => (
                  <button
                    key={lang.code}
                    role="option"
                    aria-selected={i18n.language.startsWith(lang.code)}
                    onClick={() => selectLanguage(lang.code)}
                    className={`w-full text-left px-4 py-2.5 text-sm flex items-center justify-between hover:bg-gray-50 transition ${
                      i18n.language.startsWith(lang.code) ? 'bg-mtn-yellow/10 font-bold text-mtn-blue' : 'text-gray-700'
                    }`}
                  >
                    <span>{lang.native}</span>
                    <span className="text-xs text-gray-400">{lang.name}</span>
                  </button>
                ))}
              </div>
            ))}
            {filtered.length === 0 && (
              <div className="p-4 text-center text-sm text-gray-400">
                No languages found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
