import { reactive } from 'vue';
import en from './en.js';
import ms from './ms.js';

const savedLocale = localStorage.getItem('arus_lang') || 'en';

const state = reactive({
  locale: savedLocale,
});

const messages = { en, ms };

// Sync saved language to backend on load
fetch('/api/config/language', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ language: savedLocale }),
}).catch(() => {});

export function t(key) {
  return messages[state.locale]?.[key] || messages['en'][key] || key;
}

export function setLocale(lang) {
  state.locale = lang;
  localStorage.setItem('arus_lang', lang);
  // Sync with backend
  fetch('/api/config/language', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language: lang }),
  }).catch(() => {});
}

export function getLocale() {
  return state.locale;
}
