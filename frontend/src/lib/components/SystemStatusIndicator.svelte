<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { _ } from 'svelte-i18n';

  import { api } from '$lib/api';

  type SystemStatus = {
    online: boolean;
    last_webhook_timestamp: string | null;
    checked_at: string;
  };

  let online = $state(false);
  let lastWebhookTimestamp = $state<string | null>(null);
  let timer: number | undefined;

  async function refreshStatus(): Promise<void> {
    try {
      const data = await api.get<SystemStatus>('/system/status');
      online = data.online;
      lastWebhookTimestamp = data.last_webhook_timestamp;
    } catch {
      online = false;
    }
  }

  onMount(async () => {
    await refreshStatus();
    timer = window.setInterval(refreshStatus, 15000);
  });

  onDestroy(() => {
    if (timer) {
      window.clearInterval(timer);
    }
  });
</script>

<div data-testid="system-status" class="flex items-center gap-2 rounded border border-gray-300 px-3 py-2 text-xs">
  <span class={online ? 'h-2 w-2 rounded-full bg-green-500' : 'h-2 w-2 rounded-full bg-red-500'}></span>
  <span>{online ? $_('layout.systemOnline') : $_('layout.systemOffline')}</span>
  {#if lastWebhookTimestamp}
    <span class="text-gray-500">({new Date(lastWebhookTimestamp).toLocaleTimeString()})</span>
  {/if}
</div>
