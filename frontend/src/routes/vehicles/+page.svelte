<script lang="ts">
  import { onMount } from 'svelte';
  import { _ } from 'svelte-i18n';
  import { get } from 'svelte/store';

  import { api } from '$lib/api';

  type VehicleStatus = 'allowed' | 'blocked';
  type Vehicle = {
    id: number;
    license_plate: string;
    status: VehicleStatus;
    owner_info: string | null;
  };

  type VehicleList = {
    items: Vehicle[];
    total: number;
    limit: number;
    offset: number;
  };

  const plateRegex = /^[A-Z0-9]{3,12}$/;

  let vehicles: Vehicle[] = $state([]);
  let errorMessage = $state('');
  let loading = $state(true);

  let showModal = $state(false);
  let editingId: number | null = $state(null);
  let formPlate = $state('');
  let formStatus: VehicleStatus = $state('blocked');
  let formOwnerInfo = $state('');
  let formError = $state('');

  onMount(loadVehicles);

  async function loadVehicles(): Promise<void> {
    loading = true;
    errorMessage = '';
    try {
      const data = await api.get<VehicleList>('/vehicles?limit=200&offset=0');
      vehicles = data.items;
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'vehicles.failedLoad';
    } finally {
      loading = false;
    }
  }

  function openCreateModal(): void {
    editingId = null;
    formPlate = '';
    formStatus = 'blocked';
    formOwnerInfo = '';
    formError = '';
    showModal = true;
  }

  function openEditModal(vehicle: Vehicle): void {
    editingId = vehicle.id;
    formPlate = vehicle.license_plate;
    formStatus = vehicle.status;
    formOwnerInfo = vehicle.owner_info ?? '';
    formError = '';
    showModal = true;
  }

  async function submitVehicle(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    formError = '';

    const normalizedPlate = formPlate.replace(/\s+/g, '').toUpperCase();
    if (!plateRegex.test(normalizedPlate)) {
      formError = 'vehicles.plateValidation';
      return;
    }

    const payload = {
      license_plate: normalizedPlate,
      status: formStatus,
      owner_info: formOwnerInfo || null
    };

    try {
      if (editingId === null) {
        await api.post('/vehicles', payload);
      } else {
        await api.put(`/vehicles/${editingId}`, payload);
      }
      showModal = false;
      await loadVehicles();
    } catch (error) {
      formError = error instanceof Error ? error.message : 'vehicles.failedSave';
    }
  }

  async function removeVehicle(id: number): Promise<void> {
    if (!confirm(get(_)('vehicles.confirmDelete'))) {
      return;
    }

    try {
      await api.delete(`/vehicles/${id}`);
      await loadVehicles();
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'vehicles.failedDelete';
    }
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between">
    <h1 class="text-2xl font-bold">{$_('vehicles.title')}</h1>
    <button class="rounded bg-black px-4 py-2 text-white" onclick={openCreateModal}>{$_('vehicles.add')}</button>
  </div>

  {#if loading}
    <p>{$_('common.loading')}</p>
  {:else if errorMessage}
    <p class="text-red-600">{$_(errorMessage)}</p>
  {:else}
    <div class="overflow-x-auto rounded border border-gray-200 bg-white">
      <table class="min-w-full text-left text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="px-4 py-2">{$_('vehicles.plate')}</th>
            <th class="px-4 py-2">{$_('common.status')}</th>
            <th class="px-4 py-2">{$_('vehicles.owner')}</th>
            <th class="px-4 py-2">{$_('common.actions')}</th>
          </tr>
        </thead>
        <tbody>
          {#each vehicles as vehicle}
            <tr class="border-t border-gray-100">
              <td class="px-4 py-2">{vehicle.license_plate}</td>
              <td class="px-4 py-2">{vehicle.status === 'allowed' ? $_('vehicles.allowed') : $_('vehicles.blocked')}</td>
              <td class="px-4 py-2">{vehicle.owner_info ?? $_('vehicles.emptyOwner')}</td>
              <td class="px-4 py-2">
                <div class="flex gap-2">
                  <button class="rounded border border-gray-300 px-2 py-1" onclick={() => openEditModal(vehicle)}>{$_('common.edit')}</button>
                  <button class="rounded border border-red-300 px-2 py-1 text-red-700" onclick={() => removeVehicle(vehicle.id)}>{$_('common.delete')}</button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

{#if showModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
    <div class="w-full max-w-md rounded bg-white p-4">
      <h2 class="mb-3 text-lg font-bold">{editingId === null ? $_('vehicles.addTitle') : $_('vehicles.editTitle')}</h2>
      <form class="space-y-3" onsubmit={submitVehicle}>
        <label class="block">
          <span class="mb-1 block text-sm">{$_('vehicles.plateLabel')}</span>
          <input class="w-full rounded border border-gray-300 px-3 py-2" placeholder="ABC123" bind:value={formPlate} required />
        </label>

        <label class="block">
          <span class="mb-1 block text-sm">{$_('common.status')}</span>
          <select class="w-full rounded border border-gray-300 px-3 py-2" bind:value={formStatus}>
            <option value="allowed">{$_('vehicles.allowed')}</option>
            <option value="blocked">{$_('vehicles.blocked')}</option>
          </select>
        </label>

        <label class="block">
          <span class="mb-1 block text-sm">{$_('vehicles.ownerInfo')}</span>
          <input class="w-full rounded border border-gray-300 px-3 py-2" bind:value={formOwnerInfo} />
        </label>

        {#if formError}
          <p class="text-sm text-red-600">{$_(formError)}</p>
        {/if}

        <div class="flex justify-end gap-2">
          <button type="button" class="rounded border border-gray-300 px-4 py-2" onclick={() => (showModal = false)}>{$_('common.cancel')}</button>
          <button type="submit" class="rounded bg-black px-4 py-2 text-white">{$_('common.save')}</button>
        </div>
      </form>
    </div>
  </div>
{/if}
