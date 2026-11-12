import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // В разработке фронтенд и backend на разных портах. Прокси делаем
    // запросы к /api на backend, чтобы браузер считал их same-origin
    // (тогда httpOnly-кука работает так же, как в проде).
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
