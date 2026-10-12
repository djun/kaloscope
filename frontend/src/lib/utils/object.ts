/**
 * Return a record only when it still has keys.
 *
 * @param record - Record to compact.
 * @returns The original record, or `null` when empty.
 */
export function compactRecord<T>(record: Record<string, T>): Record<string, T> | null {
  return Object.keys(record).length ? record : null;
}
