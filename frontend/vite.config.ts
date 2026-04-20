import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: '/ui/assets/',
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true
  }
})
