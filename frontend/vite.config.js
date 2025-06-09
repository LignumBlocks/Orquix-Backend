import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  
  // Configuración para build de producción
  build: {
    outDir: 'dist',
    sourcemap: false, // Desactivar sourcemaps en producción
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['lucide-react'],
          utils: ['axios']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  
  // Configuración de optimización
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios', 'lucide-react']
  },
  
  // Configuración del servidor de desarrollo
  server: {
    port: 5173,
    host: true, // Permite conexiones externas en desarrollo
    proxy: {
      // Proxy para todas las requests de la API en desarrollo
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        followRedirects: true,
        headers: {
          'Origin': 'http://localhost:5173'
        },
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🚨 Proxy error:', err.message);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('📤 Sending Request:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('📥 Received Response:', proxyRes.statusCode, req.url);
          });
        },
      }
    }
  },
  
  // Configuración para preview
  preview: {
    port: 4173,
    host: true
  }
})
