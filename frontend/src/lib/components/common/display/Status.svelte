<script lang="ts" module>
  export type StatusProps = {
    /**
     * Status rate, a number between 0 and 1.
     * If null or undefined, the status will be displayed as inactive.
     */
    rate?: number | null;
    /** The animation type. */
    animation?: keyof typeof ANIMATIONS;
    /** The size of the status indicator. */
    size?: string;
    /** The class names for the container. */
    class?: string;
  };

  // the animation class names
  const ANIMATIONS = {
    none: '',
    ping: 'animate-ping',
    bounce: 'animate-bounce'
  };
</script>

<script lang="ts">
  let { rate, animation = 'ping', size = '0.5rem', class: _class }: StatusProps = $props();

  let statusClass: string = $derived.by(() => {
    if (rate === null || rate === undefined) {
      return '';
    } else if (rate <= 0) {
      return 'status-error';
    } else if (rate >= 1) {
      return 'status-success';
    }
    return 'status-warning';
  });

  let animationClass: string = $derived(statusClass ? ANIMATIONS[animation] : '');
</script>

<div class="inline-grid *:[grid-area:1/1] {_class}">
  {#if animationClass === 'animate-ping'}
    <div class="status {statusClass}" style:width={size} style:height={size}></div>
  {/if}
  <div class="status {statusClass} {animationClass}" style:width={size} style:height={size}></div>
</div>
