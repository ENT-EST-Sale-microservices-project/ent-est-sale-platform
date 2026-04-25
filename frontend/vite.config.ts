import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8008',
        changeOrigin: true,
        onProxyReq: (proxyReq, req) => {
          const auth = req.headers['authorization']
          if (auth) proxyReq.setHeader('authorization', auth)
        },
      },
      '/realms': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})
