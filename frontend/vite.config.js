import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
const frontendPort = Number.parseInt(process.env.MIROFISH_FRONTEND_PORT || '3000', 10)

export default defineConfig({
  plugins: [vue()],
  server: {
    port: Number.isNaN(frontendPort) ? 3000 : frontendPort,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
