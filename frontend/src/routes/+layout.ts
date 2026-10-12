import { sniffer } from '$lib/utils/browser';
import { appendCustomStyle } from 'iconify-icon';
import { addMessages, getLocaleFromNavigator, init, register, waitLocale } from 'svelte-i18n';
import tippy, { followCursor } from 'tippy.js';
import type { LayoutLoad } from './$types';

// SvelteKit SPA mode
// https://svelte.dev/docs/kit/single-page-apps
export const ssr = false;

/**
 * Initialize shared UI defaults, language support and the user session.
 * @returns Data used by the layout or page.
 */
export const load: LayoutLoad = async () => {
  // append custom styles to the SVG icons
  // https://github.com/iconify/iconify/issues/196
  appendCustomStyle('svg [stroke-width="2"] { stroke-width: 1.5; }');

  // set the default props for every new tippy instance
  // https://atomiks.github.io/tippyjs/v6/methods/#setdefaultprops
  tippy.setDefaultProps({
    zIndex: 9997,
    maxWidth: 300,
    arrow: false,
    theme: 'default',
    animation: 'scale',
    placement: 'bottom',
    trigger: sniffer.isDesktop() ? 'mouseenter' : '',
    plugins: [followCursor]
  });

  // initialize the i18n library
  // https://github.com/kaisermann/svelte-i18n/blob/main/docs/Svelte-Kit.md
  registerLocale('en-US', () => import('$lib/locales/en-US.json'), 'English');
  registerLocale('zh-CN', () => import('$lib/locales/zh-CN.json'), '简体中文');
  init({
    fallbackLocale: 'en-US',
    initialLocale: localStorage.getItem('locale') || getLocaleFromNavigator()
  });
  await waitLocale();
};

/**
 * Register a locale with its loader and name.
 *
 * @param locale - Locale to register.
 * @param loader - Loader function to load the locale messages.
 * @param name - Name of the locale.
 */
function registerLocale(locale: string, loader: { (): Promise<unknown> }, name: string) {
  register(locale, loader);
  addMessages('languages', { [locale]: name });
}
