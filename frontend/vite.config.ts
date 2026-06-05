import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'

// Phase 4 Plan 01: Vite dev proxy → Flask :5000 (RESEARCH.md Pattern 1).
// Critical:
//   - ws: true on /socket.io is required for Engine.IO upgrade (Pitfall #2)
//   - /static proxy is required for audio MP3s in dev (Pitfall #5)
//   - sourcemap: false on prod build per V14 ASVS configuration
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api':       { target: 'http://localhost:5000', changeOrigin: true },
      '/socket.io': { target: 'http://localhost:5000', ws: true, changeOrigin: true },
      '/static':    { target: 'http://localhost:5000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
  },
})
