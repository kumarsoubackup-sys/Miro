import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN.json'
import en from './locales/en.json'

export const LOCALE_STORAGE_KEY = 'locale'

const savedLocale = localStorage.getItem(LOCALE_STORAGE_KEY) || 'en'
const supportedLocales = ['zh-CN', 'en']
const initialLocale = supportedLocales.includes(savedLocale) ? savedLocale : 'en'

const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: 'en',
  messages: {
    'zh-CN': zhCN,
    en
  }
})

/**
 * Apply current locale to document: lang attribute and <title>
 * Call on app init and whenever locale changes.
 */
export function applyLocaleToDocument () {
  const locale = i18n.global.locale.value
  document.documentElement.lang = locale === 'zh-CN' ? 'zh-CN' : 'en'
  document.title = i18n.global.t('common.appTitle')
}

export default i18n
