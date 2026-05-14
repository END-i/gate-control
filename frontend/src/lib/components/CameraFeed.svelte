<script lang="ts">
  import Hls from 'hls.js';
  import { onDestroy, onMount } from 'svelte';

  // The HLS stream URL is injected at build time from the environment.
  // Set VITE_CAMERA_HLS_URL to e.g. http://localhost:8888/camera/index.m3u8
  // Leave it unset or set to "disabled" to hide this component entirely.
  const hlsUrl = import.meta.env.VITE_CAMERA_HLS_URL as string | undefined;
  const enabled = hlsUrl && hlsUrl !== 'disabled';

  let videoEl: HTMLVideoElement | undefined = $state();
  let hls: Hls | null = null;

  onMount(() => {
    if (!enabled || !videoEl) return;

    if (Hls.isSupported()) {
      hls = new Hls({ lowLatencyMode: true });
      hls.loadSource(hlsUrl as string);
      hls.attachMedia(videoEl);
    } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS (Safari)
      videoEl.src = hlsUrl as string;
    }
  });

  onDestroy(() => {
    hls?.destroy();
  });
</script>

{#if enabled}
  <div class="overflow-hidden rounded border border-gray-200 bg-black">
    <!-- svelte-ignore a11y_media_has_caption -->
    <video
      bind:this={videoEl}
      class="w-full"
      autoplay
      muted
      playsinline
    ></video>
  </div>
{/if}
