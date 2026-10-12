import { debounce } from '$lib/utils/timing';
import Cropper from 'cropperjs';
import type { ActionReturn } from 'svelte/action';
import type { Instance, Props } from 'tippy.js';
import tippy from 'tippy.js';

/**
 * A Svelte action to portal an element to a specified parent element.
 *
 * @param target - The target element.
 * @param parent - The parent element to append the target to.
 * @returns The Svelte action return.
 */
export function portal(target: HTMLElement, parent?: HTMLElement): ActionReturn {
  (parent || document.body).appendChild(target);
  return {
    destroy: () => {
      if (target.parentNode) {
        target.parentNode.removeChild(target);
      }
    }
  };
}

/**
 * A Svelte action to create a tooltip using Tippy.js.
 *
 * @param target - The target element.
 * @param props - The Tippy.js properties.
 * @returns The Svelte action return.
 */
export function tooltip(target: HTMLElement, props: Partial<Props>): ActionReturn<Partial<Props>> {
  let instance: Instance | null = null;
  if (props && props.content) {
    // check if the target is inside a dialog element
    let el: HTMLElement | null = target;
    while (el && el.nodeName !== 'DIALOG') {
      el = el.parentElement;
    }
    const dialog = el as HTMLDialogElement | null;
    if (dialog) {
      // set the `appendTo` prop to the dialog element
      props.appendTo = dialog;
    }
    // create the tooltip instance if the content is provided
    instance = tippy(target, props);
  }
  return {
    update: (props) => {
      if (props && props.content) {
        if (instance) {
          instance.setProps(props);
        } else {
          instance = tippy(target, props);
        }
      } else if (instance) {
        instance.destroy();
        instance = null;
      }
    },
    destroy: () => {
      if (instance) {
        instance.destroy();
      }
    }
  };
}

/**
 * A Svelte action to create a Cropper.js instance.
 *
 * @param target - The target image element.
 * @param transform - The transform event handler.
 * @returns The Svelte action return.
 */
export function cropper(target: HTMLImageElement, transform: (blob: Promise<Blob | null>) => void): ActionReturn {
  // add 2px to the size to avoid the border
  const size = `${Math.max(target.width, target.height) + 2}px`;
  // create the Cropper.js instance
  const instance = new Cropper(target);
  const image = instance.getCropperImage();
  const canvas = instance.getCropperCanvas();
  const selection = instance.getCropperSelection();
  if (canvas) {
    canvas.background = false;
    canvas.style.minWidth = size;
    canvas.style.minHeight = size;
  }
  if (selection) {
    selection.initialCoverage = 1;
    selection.movable = false;
    selection.resizable = false;
    selection.style.minWidth = size;
    selection.style.minHeight = size;
  }
  const _transform = debounce(() =>
    transform(
      new Promise((resolve, reject) => {
        if (!selection || !selection.isConnected) {
          resolve(null);
        } else {
          selection.$toCanvas().then(
            (canvas) => canvas.toBlob((blob) => resolve(blob), 'image/webp'),
            (error) => reject(error)
          );
        }
      })
    )
  );
  image?.addEventListener('transform', _transform);
  return {
    destroy: () => {
      image?.removeEventListener('transform', _transform);
      instance.destroy();
    }
  };
}
