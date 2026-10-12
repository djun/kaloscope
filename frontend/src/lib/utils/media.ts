import { MEDIA_STREAM_PREFIX } from '$lib/constants';
import type { MediaItem, TranscodeOptions } from '$lib/types';
import Shaka from 'xgplayer-shaka';
import type { IUrl } from 'xgplayer/es/defaultConfig';

/**
 * Extract the decoded file path from a media stream URL.
 *
 * @param url - A stream URL starting with `MEDIA_STREAM_PREFIX`.
 * @returns The decoded file path, or the original string if not a stream URL.
 * @throws {URIError} If the encoded file path is malformed.
 */
export function extractStreamPath(url: string): string {
  if (!url.startsWith(MEDIA_STREAM_PREFIX)) {
    return url;
  }
  const pathWithParams = url.slice(MEDIA_STREAM_PREFIX.length);
  return decodeURIComponent(pathWithParams.split('&')[0]);
}

/**
 * Build a media stream URL with optional transcode parameters.
 *
 * @param path - The file path to stream.
 * @param transcode - Optional transcode options.
 * @returns The full stream URL with query parameters.
 */
export function buildStreamUrl(path: string, transcode: TranscodeOptions | null = null): string {
  let url = `${MEDIA_STREAM_PREFIX}${encodeURIComponent(path)}`;
  if (transcode) {
    url += `&transcode=true`;
    url += `&quality=${transcode.quality}`;
    url += `&resolution=${transcode.resolution}`;
    if (transcode.hwaccel) {
      url += `&hwaccel=${transcode.hwaccel}`;
    }
  }
  return url;
}

/**
 * Check if a media URL is a transcoded stream.
 *
 * @param url - The media URL to check.
 * @returns Whether the URL is a transcoded stream.
 */
export function isTranscodedStream(url: IUrl | null | undefined): boolean {
  return typeof url === 'string' && url.startsWith(MEDIA_STREAM_PREFIX) && url.includes('transcode=true');
}

/**
 * Check whether the current browser can play the DASH streams.
 *
 * @returns Whether Shaka and the required MediaSource codecs are supported.
 */
export function isDashSupported(): boolean {
  const mediaSource = globalThis.MediaSource;
  if (!Shaka.isSupported() || !mediaSource?.isTypeSupported) {
    return false;
  }
  const dashMediaTypes = ['video/mp4; codecs="avc1.640028"', 'audio/mp4; codecs="mp4a.40.2"'];
  return dashMediaTypes.every((type) => mediaSource.isTypeSupported(type));
}

/**
 * Format the media title with season and episode if available.
 *
 * @param item - The media item, or null/undefined when unavailable.
 * @returns The title with season and episode when present, or an empty string for a missing item.
 */
export function mediaTitle(item: MediaItem | null | undefined): string {
  if (!item) {
    return '';
  }
  const title = item.title ?? item.name;
  if (item.season !== null && item.episode !== null) {
    return `S${item.season}E${item.episode} - ${title}`;
  }
  return title;
}
