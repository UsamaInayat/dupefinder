import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '..')

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@login-root': path.resolve(repoRoot, 'login.png'),
    },
  },
  server: {
    port: 3000,
    fs: {
      allow: [repoRoot],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
