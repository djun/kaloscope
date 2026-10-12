/**
 * Normalize a URL pathname by stripping the trailing slash.
 *
 * @param pathname - The pathname to normalize.
 * @returns The normalized pathname (root `/` is preserved).
 */
export function normalizePathname(pathname: string): string {
  return pathname.replace(/\/$/, '') || '/';
}

/**
 * Trim a URL and separate its optional HTTP or HTTPS prefix.
 *
 * @param value - The URL text, which may omit a scheme.
 * @returns The remaining URL and a secure flag that is `null` when no HTTP scheme is present.
 */
export function splitHttpUrl(value: string | null | undefined): { url: string; secure: boolean | null } {
  const url = value?.trim() ?? '';
  if (url.toLowerCase().startsWith('http://')) {
    return { url: url.slice(7), secure: false };
  }
  if (url.toLowerCase().startsWith('https://')) {
    return { url: url.slice(8), secure: true };
  }
  return { url, secure: null };
}
