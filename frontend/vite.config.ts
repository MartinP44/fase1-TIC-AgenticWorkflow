import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Use environment variable for backend URL in Docker, default to localhost for local dev
const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true, // Allow external connections inside Docker container
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        // SSE / streaming: desactivar buffering y aumentar timeout
        ws: false,
        configure: (proxy) => {
          proxy.on('proxyReq', (_proxyReq, req) => {
            // Evitar que el proxy bufferice respuestas SSE
            if (req.headers.accept?.includes('text/event-stream')) {
              _proxyReq.setHeader('Cache-Control', 'no-cache')
            }
          })
          proxy.on('error', (err) => {
            console.error('[vite-proxy] error:', err.message)
          })
        },
      },
    },
  },
})

