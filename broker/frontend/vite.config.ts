import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { Agent } from 'http'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: '0.0.0.0',
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        agent: new Agent({ keepAlive: true }),
      },
    },
  },
})
