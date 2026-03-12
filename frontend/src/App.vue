<template>
  <div class="app-wrap">
    <router-view />
    <div class="locale-switcher">
      <button
        class="locale-btn"
        :class="{ active: locale === 'en' }"
        @click="setLocale('en')"
      >EN</button>
      <span class="locale-sep">|</span>
      <button
        class="locale-btn"
        :class="{ active: locale === 'zh' }"
        @click="setLocale('zh')"
      >中文</button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { setLocale } from './i18n'

const { locale } = useI18n()
</script>

<style>
.app-wrap {
  position: relative;
  min-height: 100vh;
}

.locale-switcher {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(0,0,0,0.06);
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 13px;
}

.locale-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  color: #666;
  font-weight: 500;
}

.locale-btn:hover {
  color: #000;
  background: rgba(0,0,0,0.06);
}

.locale-btn.active {
  color: #000;
  background: rgba(255,255,255,0.9);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.1);
}

.locale-sep {
  color: #999;
  user-select: none;
}

/* Global resets */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #000000;
  background-color: #ffffff;
}

/* Scrollbar styles */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #000000;
}

::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

/* Global button styles */
button {
  font-family: inherit;
}
</style>
