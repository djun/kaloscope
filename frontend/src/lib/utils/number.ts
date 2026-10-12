/**
 * Calculate an aspect ratio from a number or CSS ratio string.
 *
 * @param ratio - A number or CSS ratio such as `16/9`, `9/16`, `0.75`, or `auto`.
 * @returns The nonnegative ratio, or `0` for empty or `auto` values; malformed numbers may produce `NaN`.
 */
export function aspectRatio(ratio: number | string | null | undefined): number {
  if (typeof ratio === 'number') {
    return Math.max(0, ratio);
  }
  if (!ratio || ratio.trim().toLowerCase() === 'auto') {
    return 0;
  }
  try {
    const [w, h = '1'] = ratio.split('/');
    return Math.max(0, Number(w) / Number(h));
  } catch {
    return 0;
  }
}

/**
 * Convert a number to a fixed decimal string with bounds checking.
 *
 * @param value - Numeric value or string to format, or `null` or `undefined`.
 * @param decimals - Number of decimal places to include (default is `1`).
 * @param min - Lower bound, or `null` to omit it; a bound of `0` produces an empty string.
 * @param max - Upper bound, or `null` to omit it.
 * @returns A string representing the fixed number, or an empty string if the input is invalid.
 */
export function fixedNumber(
  value: number | string | null | undefined,
  decimals: number = 1,
  min: number | null = null,
  max: number | null = null
): string {
  if (value === null || value === undefined) {
    return '';
  }
  const num = Number(value);
  if (Number.isNaN(num)) {
    return '';
  }
  if (min !== null && num <= min) {
    // `min=0` returns an empty string instead of `"0"`
    // which is more suitable for rating displays
    return min ? min.toString() : '';
  }
  if (max !== null && num >= max) {
    return max.toString();
  }
  return num.toFixed(decimals);
}
