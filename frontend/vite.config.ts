import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 開發時把 /api 轉給 Functions emulator(design.md 第 7.4 節)
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001/demo-aiguide/asia-east1/api',
        changeOrigin: true,
      },
    },
  },
})
