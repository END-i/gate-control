<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { _ } from 'svelte-i18n';
  import { get } from 'svelte/store';

  import ImageModal from '$lib/components/ImageModal.svelte';
  import { api } from '$lib/api';
  import { authToken } from '$lib/stores/auth';

  type AccessLog = {
    id: number;
    license_plate: string;
    timestamp: string;
    access_granted: boolean;
    image_path: string | null;
  };

  type AccessLogList = {
    items: AccessLog[];
    total: number;
    limit: number;
    offset: number;
  };

  const pageSize = 20;
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

  let logs: AccessLog[] = $state([]);
  let loading = $state(true);
  let errorMessage = $state('');

  let total = $state(0);
  let offset = $state(0);

  let filterPlate = $state('');
  let filterDateFrom = $state('');
  let filterDateTo = $state('');

  let imageModalOpen = $state(false);
  let activeImageUrl = $state('');

  let eventSource: EventSource | null = null;

  onMount(async () => {
    await loadLogs();
    await connectSSE();
  });

  onDestroy(() => {
    if (eventSource) {
      eventSource.close();
    }
  });

  function buildQuery(currentOffset: number): string {
    const params = new URLSearchParams({
      limit: String(pageSize),
      offset: String(currentOffset)
    });

    if (filterPlate.trim()) {
      params.set('plate', filterPlate.trim().toUpperCase());
    }
    if (filterDateFrom) {
      params.set('date_from', new Date(filterDateFrom).toISOString());
    }
    if (filterDateTo) {
      params.set('date_to', new Date(filterDateTo).toISOString());
    }

    return params.toString();
  }

  async function loadLogs(newOffset = offset): Promise<void> {
    loading = true;
    errorMessage = '';

    try {
      const data = await api.get<AccessLogList>(`/logs?${buildQuery(newOffset)}`);
      logs = data.items;
      total = data.total;
      offset = data.offset;
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'logs.failed';
    } finally {
      loading = false;
    }
  }

  async function applyFilters(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    await loadLogs(0);
  }

  async function previousPage(): Promise<void> {
    if (offset === 0) {
      return;
    }
    await loadLogs(Math.max(0, offset - pageSize));
  }

  async function nextPage(): Promise<void> {
    if (offset + pageSize >= total) {
      return;
    }
    await loadLogs(offset + pageSize);
  }

  function openImage(path: string | null): void {
    if (!path) {
      return;
    }

    activeImageUrl = `${apiBaseUrl.replace('/api', '')}/${path}`;
    imageModalOpen = true;
  }

  function closeImage(): void {
    imageModalOpen = false;
    activeImageUrl = '';
  }

  function downloadCsv(): void {
    const headers = ['id', 'timestamp', 'license_plate', 'access_granted', 'image_path'];
    const rows = logs.map((entry) => [
      entry.id,
      entry.timestamp,
      entry.license_plate,
      entry.access_granted,
      entry.image_path ?? ''
    ]);

    const csv = [headers, ...rows]
      .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `logs-${new Date().toISOString()}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function connectSSE(): Promise<void> {
    const token = get(authToken);
    if (!token) return;

    let sseToken: string;
    try {
      const data = await api.post<{ sse_token: string }>('/logs/stream-token');
      sseToken = data.sse_token;
    } catch {
      return;
    }

    const streamUrl = `${apiBaseUrl}/logs/stream?access_token=${encodeURIComponent(sseToken)}`;
    eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
      try {
        const incoming = JSON.parse(event.data) as AccessLog;
        logs = [incoming, ...logs.filter((item) => item.id !== incoming.id)].slice(0, pageSize);
        total += 1;
      } catch {
        // Ignore malformed event payloads.
      }
    };

    eventSource.onerror = () => {
      eventSource?.close();
      eventSource = null;
    };
  }
</script>

<div class="space-y-4">
  <div class="flex flex-wrap items-center justify-between gap-2">
    <h1 class="text-2xl font-bold">{$_('logs.title')}</h1>
    <button class="rounded border border-gray-300 px-4 py-2" onclick={downloadCsv}>{$_('logs.downloadCsv')}</button>
  </div>

  <form class="grid gap-2 rounded border border-gray-200 bg-white p-4 md:grid-cols-4" onsubmit={applyFilters}>
    <input
      class="rounded border border-gray-300 px-3 py-2"
      placeholder="Plate"
      bind:value={filterPlate}
    />
    <input class="rounded border border-gray-300 px-3 py-2" type="datetime-local" bind:value={filterDateFrom} />
    <input class="rounded border border-gray-300 px-3 py-2" type="datetime-local" bind:value={filterDateTo} />
    <button class="rounded bg-black px-4 py-2 font-semibold text-white" type="submit">{$_('logs.applyFilters')}</button>
  </form>

  {#if loading}
    <p>{$_('common.loading')}</p>
  {:else if errorMessage}
    <p class="text-red-600">{$_(errorMessage)}</p>
  {:else}
    <div class="overflow-x-auto rounded border border-gray-200 bg-white">
      <table class="min-w-full text-left text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="px-4 py-2">{$_('logs.time')}</th>
            <th class="px-4 py-2">{$_('logs.plate')}</th>
            <th class="px-4 py-2">{$_('common.status')}</th>
            <th class="px-4 py-2">{$_('logs.photo')}</th>
          </tr>
        </thead>
        <tbody>
          {#each logs as log}
            <tr class="border-t border-gray-100">
              <td class="px-4 py-2">{new Date(log.timestamp).toLocaleString()}</td>
              <td class="px-4 py-2">{log.license_plate}</td>
              <td class="px-4 py-2">
                <span class={log.access_granted ? 'text-green-700' : 'text-red-700'}>
                  {log.access_granted ? $_('logs.allowed') : $_('logs.denied')}
                </span>
              </td>
              <td class="px-4 py-2">
                {#if log.image_path}
                  <button class="rounded border border-gray-300 px-2 py-1" onclick={() => openImage(log.image_path)}>{$_('logs.view')}</button>
                {:else}
                  -
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between">
      <p class="text-sm text-gray-600">{$_('logs.showing', { values: { from: offset + 1, to: Math.min(offset + pageSize, total), total } })}</p>
      <div class="flex gap-2">
        <button class="rounded border border-gray-300 px-3 py-1" disabled={offset === 0} onclick={previousPage}>{$_('logs.prev')}</button>
        <button
          class="rounded border border-gray-300 px-3 py-1"
          disabled={offset + pageSize >= total}
          onclick={nextPage}
        >
          {$_('logs.next')}
        </button>
      </div>
    </div>
  {/if}
</div>

<ImageModal open={imageModalOpen} imageUrl={activeImageUrl} onClose={closeImage} />
