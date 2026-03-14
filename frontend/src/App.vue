<template>
  <div class="lang-fab" @click="toggleLang">
    {{ getLocale() === 'en' ? 'EN' : 'MS' }}
  </div>
  <router-view />
</template>

<script setup>
import { setLocale, getLocale } from './i18n/index.js';

const toggleLang = () => {
  setLocale(getLocale() === 'en' ? 'ms' : 'en');
};
</script>

<style>
/* Global reset */
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

/* Scrollbar styling */
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

/* Global button styling */
button {
  font-family: inherit;
}

/* Floating language toggle */
.lang-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  background: #000;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  z-index: 9999;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: background 0.2s, transform 0.2s;
  user-select: none;
}

.lang-fab:hover {
  background: #FF4500;
  transform: scale(1.1);
}
</style>
