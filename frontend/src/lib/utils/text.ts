/**
 * Extract the first Unicode letter or number, falling back to the first character.
 *
 * @param str - Nonempty source string.
 * @returns The initial converted to the locale's uppercase form.
 * @throws {TypeError} If the source string is empty.
 */
export function extractInitial(str: string): string {
  const match = str.match(/[\p{L}\p{N}]/u);
  return (match ? match[0] : str[0]).toLocaleUpperCase();
}

/**
 * Escape HTML special characters in a string to prevent XSS attacks.
 *
 * @param str - String to escape.
 * @returns The escaped string.
 */
export function escapeHTML(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Convert part of the title to italic format.
 *
 * @param title - Title string.
 * @returns The HTML string with italicized parts.
 */
export function italic(title: string): string {
  const prefix = '<span class="text-sm font-normal opacity-60">[<span class="italic px-1">';
  const suffix = '</span>]</span>';

  const start = title.indexOf('[');
  const end = title.lastIndexOf(']');

  if (start === -1 || end <= start + 1) {
    return escapeHTML(title);
  }

  return (
    escapeHTML(title.slice(0, start)) +
    `${prefix}${escapeHTML(title.slice(start + 1, end))}${suffix}` +
    escapeHTML(title.slice(end + 1))
  );
}
