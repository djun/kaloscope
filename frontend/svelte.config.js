import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  // preprocess TypeScript and component styles
  // https://svelte.dev/docs/kit/integrations
  preprocess: vitePreprocess(),
  kit: {
    // emit static pages with an SPA fallback
    // https://svelte.dev/docs/kit/adapters
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: '404.html',
      precompress: false,
      strict: true
    }),
    paths: {
      relative: false
    },
    serviceWorker: {
      register: false
    }
  },
  compilerOptions: {
    runes: true
  }
};

export default config;
