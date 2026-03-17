import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n, { applyLocaleToDocument } from './i18n'

const app = createApp(App)

app.use(i18n)
app.use(router)

applyLocaleToDocument()

app.mount('#app')
