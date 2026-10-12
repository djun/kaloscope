// https://github.com/vite-pwa/sveltekit/issues/16
// render this page at build time because it has no dynamic data
// it so that it gets served as a static asset in production
export const prerender = true;
