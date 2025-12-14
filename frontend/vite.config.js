import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api/auth': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true
      },
      '/api/market': {
        target: 'http://127.0.0.1:8002', 
        changeOrigin: true
      },
      '/api/chat': {
        target: 'http://127.0.0.1:8003',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://127.0.0.1:8003', 
        ws: true,
        changeOrigin: true
      }
    }
  }
})