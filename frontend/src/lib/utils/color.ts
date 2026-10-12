/**
 * Check if a color is white.
 *
 * @param color - The color string to check.
 * @returns Whether the value matches a supported white color notation.
 */
export function isWhite(color: string | null | undefined): boolean {
  if (!color) {
    return false;
  }
  // normalize the color code
  const code = color.trim().toLowerCase().replace(/\s+/g, '');
  // check common white color codes
  const whiteCodes = ['#ffffff', '#fff', 'rgb(255,255,255)', 'hsl(0,0%,100%)', 'white'];
  return whiteCodes.includes(code);
}
