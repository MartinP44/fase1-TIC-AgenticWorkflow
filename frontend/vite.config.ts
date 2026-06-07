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
      },
    },
  },
})
