<script lang="ts">
  import { onMount } from 'svelte';
  import { _ } from 'svelte-i18n';

  import { api } from '$lib/api';

  type AuditEvent = {
    id: number;
    event_type: string;
    actor: string;
    success: boolean;
    details: string;
    timestamp: string;
  };

  const LIMIT = 50;

  let items = $state<AuditEvent[]>([]);
  let total = $state(0);
  let offset = $state(0);
  let loading = $state(false);
  let errorMessage = $state('');

  // Filters
  let filterEventType = $state('');
  let filterActor = $state('');
  let filterDateFrom = $state('');
  let filterDateTo = $state('');

  async function loadPage(newOffset: number): Promise<void> {
    loading = true;
    errorMessage = '';
    try {
      const params = new URLSearchParams({ limit: String(LIMIT), offset: String(newOffset) });
      if (filterEventType) params.set('event_type', filterEventType);
      if (filterActor) params.set('actor', filterActor);
      if (filterDateFrom) params.set('date_from', new Date(filterDateFrom).toISOString());
      if (filterDateTo) params.set('date_to', new Date(filterDateTo + 'T23:59:59Z').toISOString());

      const data = await api.get<{ items: AuditEvent[]; total: number }>(`/audit?${params}`);
      items = data.items;
      total = data.total;
      offset = newOffset;
    } catch (e) {
      errorMessage = e instanceof Error ? e.message : $_('audit.failed');
    } finally {
      loading = false;
    }
  }

  function applyFilters(): void {
    loadPage(0);
  }

  function clearFilters(): void {
    filterEventType = '';
    filterActor = '';
    filterDateFrom = '';
    filterDateTo = '';
    loadPage(0);
  }

  onMount(() => loadPage(0));

  const totalPages = $derived(Math.ceil(total / LIMIT));
  const currentPage = $derived(Math.floor(offset / LIMIT) + 1);
</script>

<div class="space-y-4">
  <h1 class="text-2xl font-bold">{$_('audit.title')}</h1>

  <!-- Filters -->
  <div class="flex flex-wrap items-end gap-2 rounded border border-gray-200 bg-white p-3">
    <div class="flex flex-col gap-1">
      <label for="filter-event-type" class="text-xs text-gray-500">{$_('audit.eventType')}</label>
      <input
        id="filter-event-type"
        class="rounded border border-gray-300 px-2 py-1 text-sm"
        bind:value={filterEventType}
        placeholder="e.g. login_success"
      />
    </div>
    <div class="flex flex-col gap-1">
      <label for="filter-actor" class="text-xs text-gray-500">{$_('audit.actor')}</label>
      <input
        id="filter-actor"
        class="rounded border border-gray-300 px-2 py-1 text-sm"
        bind:value={filterActor}
        placeholder="e.g. admin"
      />
    </div>
    <div class="flex flex-col gap-1">
      <label for="filter-date-from" class="text-xs text-gray-500">{$_('logs.dateFrom')}</label>
      <input id="filter-date-from" type="date" class="rounded border border-gray-300 px-2 py-1 text-sm" bind:value={filterDateFrom} />
    </div>
    <div class="flex flex-col gap-1">
      <label for="filter-date-to" class="text-xs text-gray-500">{$_('logs.dateTo')}</label>
      <input id="filter-date-to" type="date" class="rounded border border-gray-300 px-2 py-1 text-sm" bind:value={filterDateTo} />
    </div>
    <button
      type="button"
      onclick={applyFilters}
      class="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
    >
      {$_('logs.applyFilters')}
    </button>
    <button
      type="button"
      onclick={clearFilters}
      class="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
    >
      {$_('audit.clearFilters')}
    </button>
  </div>

  {#if loading}
    <p class="text-sm text-gray-500">{$_('common.loading')}</p>
  {:else if errorMessage}
    <p class="text-sm text-red-600">{errorMessage}</p>
  {:else}
    <div class="overflow-x-auto rounded border border-gray-200 bg-white">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-50 text-xs uppercase text-gray-500">
          <tr>
            <th class="px-4 py-2 text-left">{$_('audit.time')}</th>
            <th class="px-4 py-2 text-left">{$_('audit.eventType')}</th>
            <th class="px-4 py-2 text-left">{$_('audit.actor')}</th>
            <th class="px-4 py-2 text-left">{$_('audit.result')}</th>
            <th class="px-4 py-2 text-left">{$_('audit.details')}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          {#each items as ev (ev.id)}
            <tr class="hover:bg-gray-50">
              <td class="whitespace-nowrap px-4 py-2 font-mono text-xs text-gray-500">
                {new Date(ev.timestamp).toLocaleString()}
              </td>
              <td class="px-4 py-2 font-mono text-xs">{ev.event_type}</td>
              <td class="px-4 py-2">{ev.actor}</td>
              <td class="px-4 py-2">
                <span class={ev.success
                  ? 'rounded px-1.5 py-0.5 text-xs font-medium bg-green-100 text-green-700'
                  : 'rounded px-1.5 py-0.5 text-xs font-medium bg-red-100 text-red-700'}>
                  {ev.success ? $_('audit.ok') : $_('audit.fail')}
                </span>
              </td>
              <td class="max-w-xs truncate px-4 py-2 text-xs text-gray-600" title={ev.details}>
                {ev.details}
              </td>
            </tr>
          {/each}
          {#if items.length === 0}
            <tr><td colspan="5" class="px-4 py-6 text-center text-gray-400">{$_('audit.empty')}</td></tr>
          {/if}
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    {#if total > LIMIT}
      <div class="flex items-center justify-between text-sm text-gray-600">
        <span>{$_('logs.showing', { values: { from: offset + 1, to: Math.min(offset + LIMIT, total), total } })}</span>
        <div class="flex gap-2">
          <button
            type="button"
            onclick={() => loadPage(offset - LIMIT)}
            disabled={offset === 0}
            class="rounded border px-3 py-1 disabled:opacity-40"
          >{$_('logs.prev')}</button>
          <span class="px-2 py-1">{currentPage} / {totalPages}</span>
          <button
            type="button"
            onclick={() => loadPage(offset + LIMIT)}
            disabled={offset + LIMIT >= total}
            class="rounded border px-3 py-1 disabled:opacity-40"
          >{$_('logs.next')}</button>
        </div>
      </div>
    {/if}
  {/if}
</div>
