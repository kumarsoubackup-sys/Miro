import { createI18n } from 'vue-i18n'
import zh from './locales/zh'
import en from './locales/en'

const STORAGE_KEY = 'mirofish_locale'

function getDefaultLocale() {
  try {
    return localStorage.getItem(STORAGE_KEY) || 'zh'
  } catch {
    return 'zh'
  }
}

function setStoredLocale(locale) {
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch (_) {}
}

const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'en',
  messages: { zh, en },
  globalInjection: true,
})

export function setLocale(locale) {
  i18n.global.locale.value = locale
  setStoredLocale(locale)
}

export function getLocale() {
  return i18n.global.locale.value
}

export default i18n
