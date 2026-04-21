import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react({
      // Include .js files that contain JSX (CRA convention)
      include: '**/*.{js,jsx,ts,tsx}',
    }),
  ],
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
    include: ['ghin'],
  },
  resolve: {
    alias: {
      ghin: 'ghin/dist/index.js',
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/players': { target: 'http://localhost:8000', changeOrigin: true },
      '/games': { target: 'http://localhost:8000', changeOrigin: true },
      '/courses': { target: 'http://localhost:8000', changeOrigin: true },
      '/leaderboard': { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
      '/rules': { target: 'http://localhost:8000', changeOrigin: true },
      '/messages': { target: 'http://localhost:8000', changeOrigin: true },
      '/scorecard': { target: 'http://localhost:8000', changeOrigin: true },
      '/badges': { target: 'http://localhost:8000', changeOrigin: true },
      '/banner': { target: 'http://localhost:8000', changeOrigin: true },
      '/admin': { target: 'http://localhost:8000', changeOrigin: true },
      '/data': { target: 'http://localhost:8000', changeOrigin: true },
      '/signup': { target: 'http://localhost:8000', changeOrigin: true },
      '/matchmaking': { target: 'http://localhost:8000', changeOrigin: true },
      '/email': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
  build: {
    outDir: 'build',
    assetsDir: 'static',
    sourcemap: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.js',
    css: true,
    coverage: {
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/index.js', 'src/reportWebVitals.js', 'src/**/*.d.ts', 'src/test-utils/**'],
      thresholds: {
        branches: 1,
        functions: 1,
        lines: 1,
        statements: 1,
      },
    },
  },
});
