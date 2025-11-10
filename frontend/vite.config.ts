import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175, // Set to the same port you were using
    host: true, // Allow external connections
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/analytics': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/providers': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/cache': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/alerts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/rate-limits': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
