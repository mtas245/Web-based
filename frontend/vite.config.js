import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    proxy: {
      '/api': process.env.EDUSUB_E2E === '1' ? 'http://127.0.0.1:18000' : 'http://127.0.0.1:8000',
    },
  },
})
