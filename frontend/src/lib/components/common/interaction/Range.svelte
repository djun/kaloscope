<script lang="ts" module>
  export type RangeProps = {
    /** The current value of the range input. */
    value: number;
    /** The array of values to display below the range input. */
    values?: (number | string)[];
    /** The minimum value of the range input. */
    min?: number;
    /** The maximum value of the range input. */
    max?: number;
    /** The step interval of the range input. */
    step?: number;
    /** The unit to display next to the value. */
    unit?: string;
    /** The class names for the container. */
    class?: string;
    textClass?: string;
    sliderClass?: string;
    /** The value change event handler. */
    onchange?: (value: number) => void;
  };
</script>

<script lang="ts">
  import { debounce } from '$lib/utils/timing';

  let {
    value = $bindable(),
    values,
    min = 0,
    max = 100,
    step: _step,
    unit = '%',
    class: _class,
    textClass,
    sliderClass,
    onchange
  }: RangeProps = $props();

  // calculate the step based on the values array
  let step: number | undefined = $derived.by(() => {
    if (values && values.length > 1) {
      return 100 / (values.length - 1);
    }
    return _step;
  });

  // the change event handler
  const _onchange = () => {
    if (onchange) {
      if (values && step) {
        onchange(Number(values[Math.round(value / step)]));
      } else {
        onchange(value);
      }
    }
  };

  // the debounced change event handler
  const __onchange = debounce(_onchange);
</script>

<div class="w-full max-w-xs {_class}">
  <input type="range" class="range range-xs {sliderClass}" {min} {max} {step} bind:value onchange={__onchange} />
  {#if values && values.length > 1}
    <div class="mt-1 flex justify-between text-xs {textClass}">
      {#each values as v, i (i)}
        <span>{v}{unit}</span>
      {/each}
    </div>
  {:else}
    <div class="relative mt-1 h-4 w-[calc(100%-2rem)]">
      <span class="absolute text-xs {textClass}" style="left:calc({((value - min) / (max - min)) * 100}%);">
        {value}{unit}
      </span>
    </div>
  {/if}
</div>
