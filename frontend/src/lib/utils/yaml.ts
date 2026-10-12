import { isMap, isPair, isScalar, type Document, type ParsedNode } from 'yaml';

/**
 * Move a section comment misparsed onto the last nested scalar to the following top-level key.
 *
 * The `yaml` parser may attach a comment after an empty scalar to that scalar, and `setIn` preserves it.
 *
 * @param document - The parsed YAML document to update in place.
 * @param key - The top-level mapping key whose final scalar may own the comment.
 */
export function restoreFollowingSectionComment(document: Document.Parsed<ParsedNode>, key: string) {
  if (!isMap(document.contents)) {
    return;
  }

  const entries = document.contents.items;
  const sectionIndex = entries.findIndex((entry) => isPair(entry) && isScalar(entry.key) && entry.key.value === key);
  const section = entries[sectionIndex];
  const following = entries[sectionIndex + 1];

  if (!isPair(section) || !isMap(section.value) || !isPair(following) || !isScalar(following.key)) {
    return;
  }

  const trailing = section.value.items[section.value.items.length - 1];
  if (!isPair(trailing) || !isScalar(trailing.value) || !trailing.value.spaceBefore || !trailing.value.comment) {
    return;
  }

  const comment = trailing.value.comment;
  trailing.value.comment = null;
  trailing.value.spaceBefore = false;
  following.key.commentBefore = following.key.commentBefore ? `${comment}\n${following.key.commentBefore}` : comment;
  following.key.spaceBefore = true;
}
