import { UAParser } from 'ua-parser-js';

/**
 * Extended `Document` interface for Fullscreen API methods.
 */
interface DocumentFullscreen extends Document {
  webkitFullscreenElement?: Element;
  webkitExitFullscreen?: () => void;
  webkitCurrentFullScreenElement?: Element;
  webkitCancelFullScreen?: () => void;
  mozFullScreenElement?: Element;
  mozCancelFullScreen?: () => void;
  msFullscreenElement?: Element;
  msExitFullscreen?: () => void;
}

/**
 * Extended `HTMLElement` interface for Fullscreen API methods.
 */
interface HTMLElementFullscreen extends HTMLElement {
  webkitRequestFullscreen?: () => void;
  webkitRequestFullScreen?: () => void;
  mozRequestFullScreen?: () => void;
  msRequestFullscreen?: () => void;
}

/**
 * Fullscreen API utilities.
 */
export const fullscreen = {
  /**
   * Request fullscreen mode for the document element.
   */
  enter: () => {
    const elm = document.documentElement as HTMLElementFullscreen;
    if (elm.requestFullscreen) {
      elm.requestFullscreen();
    } else if (elm.webkitRequestFullscreen) {
      elm.webkitRequestFullscreen();
    } else if (elm.webkitRequestFullScreen) {
      elm.webkitRequestFullScreen();
    } else if (elm.mozRequestFullScreen) {
      elm.mozRequestFullScreen();
    } else if (elm.msRequestFullscreen) {
      elm.msRequestFullscreen();
    }
  },
  /**
   * Exit fullscreen mode using the available browser API.
   */
  exit: () => {
    const doc = document as DocumentFullscreen;
    if (doc.exitFullscreen) {
      doc.exitFullscreen();
    } else if (doc.webkitExitFullscreen) {
      doc.webkitExitFullscreen();
    } else if (doc.webkitCancelFullScreen) {
      doc.webkitCancelFullScreen();
    } else if (doc.mozCancelFullScreen) {
      doc.mozCancelFullScreen();
    } else if (doc.msExitFullscreen) {
      doc.msExitFullscreen();
    }
  },
  /**
   * Check whether the document has a fullscreen element.
   *
   * @returns Whether a standard or vendor-prefixed fullscreen element is present.
   */
  isFullscreen: () => {
    const doc = document as DocumentFullscreen;
    return !!(
      doc.fullscreenElement ||
      doc.webkitFullscreenElement ||
      doc.webkitCurrentFullScreenElement ||
      doc.mozFullScreenElement ||
      doc.msFullscreenElement
    );
  }
};

/**
 * Parsed user agent information.
 *
 * https://docs.uaparser.dev/api/main/overview.html
 */
const { browser, device, os, ua } = UAParser(navigator.userAgent);

/**
 * Sniffer utilities.
 */
export const sniffer = {
  /**
   * Check whether the device runs iOS.
   *
   * @returns Whether the parsed operating system is iOS.
   */
  isIos: () => {
    return os.name === 'iOS';
  },
  /**
   * Check whether the device is an iPad or PlayBook.
   *
   * @returns Whether the user agent or touch-enabled Mac platform matches a tablet.
   */
  isIpad: () => {
    // https://github.com/bytedance/xgplayer/blob/main/packages/xgplayer/src/utils/sniffer.js
    return /(?:iPad|PlayBook)/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  },
  /**
   * Check whether the browser is Safari.
   *
   * @returns Whether the parsed browser is desktop or mobile Safari.
   */
  isSafari: () => {
    return browser.name === 'Safari' || browser.name === 'Mobile Safari';
  },
  /**
   * Check whether the device is a mobile phone.
   *
   * @returns Whether the parsed device type is mobile.
   */
  isMobile: () => {
    return device.type === 'mobile';
  },
  /**
   * Check whether the browser is mobile Safari.
   *
   * @returns Whether the parsed browser is mobile Safari.
   */
  isMobileSafari: () => {
    return browser.name === 'Mobile Safari';
  },
  /**
   * Check whether the device runs Android.
   *
   * @returns Whether the parsed operating system is Android or Android-x86.
   */
  isAndroid: () => {
    return os.name === 'Android' || os.name === 'Android-x86';
  },
  /**
   * Check whether the browser is Edge on Android.
   *
   * @returns Whether the parsed browser and operating system match Android Edge.
   */
  isAndroidEdge: () => {
    return (os.name === 'Android' || os.name === 'Android-x86') && browser.name === 'Edge';
  },
  /**
   * Check whether the device is a tablet.
   *
   * @returns Whether the parsed device type is a tablet.
   */
  isTablet: () => {
    return device.type === 'tablet';
  },
  /**
   * Check whether the device uses the desktop classification.
   *
   * @returns Whether the parsed device type is desktop or unspecified.
   */
  isDesktop: () => {
    return device.type === 'desktop' || !device.type;
  }
};

/**
 * Load first selected file as a base64 data URL.
 *
 * @param target - Event target of a file input change event.
 * @returns A promise resolving to the data URL or `null` when no file is selected, rejecting on read errors.
 */
export function loadFile(target: EventTarget & HTMLInputElement): Promise<string | null> {
  return new Promise((resolve, reject) => {
    if (target.files && target.files[0]) {
      const reader = new FileReader();
      reader.onload = (event) => {
        resolve(event.target?.result as string);
      };
      reader.onerror = (error) => {
        reject(error);
      };
      reader.readAsDataURL(target.files[0]);
    } else {
      resolve(null);
    }
  });
}

/**
 * Download a blob through a temporary link and release its object URL.
 *
 * @param blob - File contents to download.
 * @param filename - Suggested filename, including its extension.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  try {
    document.body.appendChild(link);
    link.click();
  } finally {
    link.remove();
    URL.revokeObjectURL(url);
  }
}
