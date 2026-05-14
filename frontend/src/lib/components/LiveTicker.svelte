<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { _ } from 'svelte-i18n';

  import { api } from '$lib/api';

  type TickerEvent = {
    id: number;
    license_plate: string;
    timestamp: string;
    access_granted: boolean;
    image_path: string | null;
  };

  const MAX_EVENTS = 20;

  let events = $state<TickerEvent[]>([]);
  let connected = $state(false);
  let errorMessage = $state('');
  let es: EventSource | null = null;
  let reconnectTimer: number | undefined;

  async function connect(): Promise<void> {
    try {
      const { sse_token } = await api.post<{ sse_token: string; expires_in: number }>(
        '/logs/stream-token'
      );
      const base = import.meta.env.VITE_API_BASE_URL as string;
      es = new EventSource(`${base}/logs/stream?access_token=${encodeURIComponent(sse_token)}`);

      es.onopen = () => {
        connected = true;
        errorMessage = '';
      };

      es.onmessage = (e) => {
        try {
          const event: TickerEvent = JSON.parse(e.data);
          events = [event, ...events].slice(0, MAX_EVENTS);
        } catch {
          // ignore parse errors
        }
      };

      es.onerror = () => {
        connected = false;
        es?.close();
        es = null;
        // SSE token expires in 60 s — reconnect after 5 s
        reconnectTimer = window.setTimeout(connect, 5000);
      };
    } catch {
      errorMessage = $_('ticker.connectFailed');
      reconnectTimer = window.setTimeout(connect, 10000);
    }
  }

  onMount(() => {
    connect();
  });

  onDestroy(() => {
    es?.close();
    if (reconnectTimer) window.clearTimeout(reconnectTimer);
  });

  function formatTime(iso: string): string {
    return new Date(iso).toLocaleTimeString();
  }
</script>

<div class="rounded border border-gray-200 bg-white p-4">
  <div class="mb-2 flex items-center justify-between">
    <h2 class="font-semibold text-gray-700">{$_('ticker.title')}</h2>
    <span class="flex items-center gap-1 text-xs">
      <span class={connected ? 'h-2 w-2 rounded-full bg-green-500' : 'h-2 w-2 rounded-full bg-gray-400'}></span>
      <span class="text-gray-500">{connected ? $_('ticker.live') : $_('ticker.connecting')}</span>
    </span>
  </div>

  {#if errorMessage}
    <p class="text-xs text-red-500">{errorMessage}</p>
  {:else if events.length === 0}
    <p class="text-xs text-gray-400">{$_('ticker.waiting')}</p>
  {:else}
    <ul class="max-h-64 divide-y divide-gray-100 overflow-y-auto text-sm">
      {#each events as ev (ev.id)}
        <li class="flex items-center gap-2 py-1">
          <span
            class={ev.access_granted
              ? 'w-14 rounded px-1 py-0.5 text-center text-xs font-medium text-green-700 bg-green-100'
              : 'w-14 rounded px-1 py-0.5 text-center text-xs font-medium text-red-700 bg-red-100'}
          >
            {ev.access_granted ? $_('ticker.allowed') : $_('ticker.denied')}
          </span>
          <span class="font-mono font-semibold">{ev.license_plate}</span>
          <span class="ml-auto text-xs text-gray-400">{formatTime(ev.timestamp)}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>
