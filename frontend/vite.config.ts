import { defineConfig } from 'vite';

export default defineConfig({server: {proxy: {
  '/v1': 'http://127.0.0.1:5000', '/health': 'http://127.0.0.1:5000'
}}, build: {sourcemap: false, rollupOptions:{onwarn(warning,warn){
  // Client-only React/Vite app: Motion's RSC boundaries are intentionally inert.
  if(warning.code==='MODULE_LEVEL_DIRECTIVE'&&warning.message.includes('use client'))return;
  warn(warning);
}}}});
