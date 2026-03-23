import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const hasPackagePath = (id: string, packageName: string) =>
  id.includes(`/node_modules/${packageName}/`) ||
  id.includes(`\\node_modules\\${packageName}\\`)

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined
          }

          if (
            hasPackagePath(id, 'react') ||
            hasPackagePath(id, 'react-dom') ||
            hasPackagePath(id, 'scheduler')
          ) {
            return 'react-vendor'
          }

          if (
            hasPackagePath(id, 'recharts') ||
            hasPackagePath(id, 'plotly.js') ||
            hasPackagePath(id, 'react-plotly.js')
          ) {
            return 'charts-vendor'
          }

          if (hasPackagePath(id, 'html-to-image')) {
            return 'export-vendor'
          }

          return 'vendor'
        },
      },
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.tsx']
  }
})
