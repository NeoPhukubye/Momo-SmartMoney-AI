import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import en from './locales/en.json';
import zu from './locales/zu.json';
import xh from './locales/xh.json';
import af from './locales/af.json';
import st from './locales/st.json';
import tn from './locales/tn.json';
import nso from './locales/nso.json';
import ts from './locales/ts.json';
import ve from './locales/ve.json';
import sw from './locales/sw.json';
import fr from './locales/fr.json';
import pt from './locales/pt.json';
import ha from './locales/ha.json';
import yo from './locales/yo.json';
import ig from './locales/ig.json';
import am from './locales/am.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      zu: { translation: zu },
      xh: { translation: xh },
      af: { translation: af },
      st: { translation: st },
      tn: { translation: tn },
      nso: { translation: nso },
      ts: { translation: ts },
      ve: { translation: ve },
      sw: { translation: sw },
      fr: { translation: fr },
      pt: { translation: pt },
      ha: { translation: ha },
      yo: { translation: yo },
      ig: { translation: ig },
      am: { translation: am },
    },
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'cookie', 'htmlTag', 'path', 'subdomain'],
      caches: ['localStorage'],
    },
  });

export default i18n;
