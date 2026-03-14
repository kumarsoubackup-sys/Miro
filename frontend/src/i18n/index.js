import { reactive } from 'vue';
import en from './en.js';
import ms from './ms.js';

const state = reactive({
  locale: localStorage.getItem('mirofish_lang') || 'en',
});

const messages = { en, ms };

export function t(key) {
  return messages[state.locale]?.[key] || messages['en'][key] || key;
}

export function setLocale(lang) {
  state.locale = lang;
  localStorage.setItem('mirofish_lang', lang);
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
