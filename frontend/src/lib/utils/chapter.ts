import type { Chapter, ChapterGroup } from '$lib/types';

/**
 * Check whether two chapter ids refer to the same chapter.
 *
 * @param left - First chapter id.
 * @param right - Second chapter id.
 * @returns Whether the ids match.
 */
export function matchChapterId(left: string | null | undefined, right: string | null | undefined) {
  return !!left && left === right;
}

/**
 * Group chapters by volume when every chapter has a volume.
 *
 * @param chapters - Chapters to group.
 * @returns Ordered chapter groups.
 */
export function groupChapters(chapters: Chapter[]): ChapterGroup[] {
  const grouped = chapters.length > 0 && chapters.every((chapter) => !!chapter.volume?.trim());
  if (!grouped) {
    return [{ volume: null, chapters }];
  }
  return chapters.reduce<ChapterGroup[]>((groups, chapter) => {
    const volume = chapter.volume!.trim();
    const group = groups.find((group) => group.volume === volume);
    if (group) {
      group.chapters.push(chapter);
    } else {
      groups.push({ volume, chapters: [chapter] });
    }
    return groups;
  }, []);
}
