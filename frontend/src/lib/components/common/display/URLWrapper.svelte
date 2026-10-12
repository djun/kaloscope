<script lang="ts" module>
  import type { Snippet } from 'svelte';
  import type { MouseEventHandler } from 'svelte/elements';

  export type URLWrapperProps = {
    /** The URL input snippet. */
    children: Snippet;
    /** Whether the URL is secure. */
    secure?: boolean;
    /** The class names for the container. */
    class?: string;
    /** The click event handler. */
    onclick?: MouseEventHandler<HTMLButtonElement>;
  };

  // the HTTP/HTTPS prefixes
  const HTTP = 'http://';
  const HTTPS = 'https://';
</script>

<script lang="ts">
  import { splitHttpUrl } from '$lib/utils/url';

  let { children, secure = $bindable(false), class: _class, onclick }: URLWrapperProps = $props();

  /**
   * Standardize the URL by trimming whitespace and removing the HTTP/HTTPS prefix.
   *
   * Update the security toggle only when the URL includes an HTTP or HTTPS prefix.
   *
   * @param url - The URL to standardize.
   * @returns The standardized URL.
   */
  export function standardize(url: string | null | undefined): string {
    const parsed = splitHttpUrl(url);
    secure = parsed.secure ?? secure;
    return parsed.url;
  }

  /**
   * Generate the full URL by adding the appropriate HTTP/HTTPS prefix.
   *
   * @param url - The URL to generate.
   * @returns The full URL with the correct protocol prefix.
   */
  export function full(url: string | null | undefined): string {
    return url ? `${secure ? HTTPS : HTTP}${url}` : '';
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<label class="input w-full gap-0 {_class}" onclick={(event) => event.preventDefault()}>
  <button
    type="button"
    class="cursor-pointer opacity-80"
    onclick={(event) => {
      secure = !secure;
      onclick?.(event);
    }}
  >
    {secure ? HTTPS : HTTP}
  </button>
  {@render children()}
</label>
