/**
 * Format an ISO 8601 datetime for a `datetime-local` input in the local timezone.
 *
 * @param value - The ISO 8601 datetime string.
 * @returns A local `yyyy-MM-ddTHH:mm` string, or an empty string for missing or invalid input.
 */
export function toDatetimeLocal(value: string | null | undefined): string {
  if (!value) {
    return '';
  }
  const date = new Date(value);
  if (isNaN(date.getTime())) {
    return '';
  }
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}
