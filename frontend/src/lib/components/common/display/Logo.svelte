<script lang="ts" module>
  type Point = [number, number];

  export type LogoProps = {
    /** The size of the logo. */
    size?: string;
    /** Whether to generate a random logo. */
    random?: boolean;
  };
</script>

<script lang="ts">
  let { size = '2.5rem', random = false }: LogoProps = $props();
  // the refresh key
  let refreshKey: number = $state(0);
  // the logo image source
  const src = new URL('/logo.svg', import.meta.url).href;

  /**
   * Trigger a refresh of the logo.
   */
  export function spin() {
    refreshKey = new Date().getTime();
    random = refreshKey % 10 !== 0;
  }

  /**
   * Generate a random SVG logo.
   *
   * @param svgElement - The SVG element.
   */
  function drawSVG(svgElement: SVGSVGElement) {
    // draw a circle
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '128');
    circle.setAttribute('cy', '128');
    circle.setAttribute('r', '122');
    circle.setAttribute('stroke', 'gray');
    circle.setAttribute('stroke-width', '9');
    circle.setAttribute('fill', 'none');
    svgElement.appendChild(circle);
    // draw some triangles
    const offset = Math.random() * 360;
    for (let i = 0; i < Math.floor(Math.random() * 5) + 1; i++) {
      svgElement.appendChild(randomTriangle(offset * i));
    }
  }

  /**
   * Generate a random triangle SVG element.
   *
   * @param offset - Triangle offset.
   * @returns The triangle SVG element.
   */
  function randomTriangle(offset: number) {
    const points: Point[] = [0, 120, 240].map((cardinal) => {
      const theta = cardinal + offset;
      const x = Math.cos((theta * Math.PI) / 180) * 110 + 128;
      const y = Math.sin((theta * Math.PI) / 180) * 110 + 128;
      return [x, y];
    });
    const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', points.map(([x, y]) => `${x},${y}`).join(' '));
    polygon.setAttribute('stroke', 'gray');
    polygon.setAttribute('stroke-width', '3');
    polygon.setAttribute('fill', randomGray());
    return polygon;
  }

  /**
   * Generate a random gray RGBA color.
   *
   * @returns The RGBA color string.
   */
  function randomGray() {
    const brightness = 200 + Math.floor(Math.random() * 56);
    const alpha = Math.random().toFixed(1);
    return `rgba(${brightness},${brightness},${brightness},${alpha})`;
  }
</script>

{#if random}
  {#key refreshKey}
    <svg use:drawSVG viewBox="0 0 256 256" class="animate-[spin_5s_linear_infinite]" width={size} height={size} />
  {/key}
{:else}
  <img {src} alt="logo" style:width={size} style:height={size} />
{/if}
