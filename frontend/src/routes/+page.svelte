<script lang="ts">
	import { onMount } from 'svelte';
	import { _ } from 'svelte-i18n';

	import { api } from '$lib/api';
	import CameraFeed from '$lib/components/CameraFeed.svelte';
	import LiveTicker from '$lib/components/LiveTicker.svelte';

	type Stats = {
		total_vehicles: number;
		today_access_total: number;
		today_denied_total: number;
		active_subscriptions: number;
		expiring_soon_count: number;
	};

	let loading = $state(true);
	let errorMessage = $state('');
	let stats: Stats = $state({
		total_vehicles: 0,
		today_access_total: 0,
		today_denied_total: 0,
		active_subscriptions: 0,
		expiring_soon_count: 0
	});

	onMount(async () => {
		try {
			stats = await api.get<Stats>('/stats');
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'dashboard.failed';
		} finally {
			loading = false;
		}
	});
</script>

<div class="space-y-4">
	<h1 class="text-2xl font-bold">{$_('dashboard.title')}</h1>

	{#if loading}
		<p>{$_('common.loading')}</p>
	{:else if errorMessage}
		<p class="text-red-600">{$_(errorMessage)}</p>
	{:else}
		<div class="grid gap-4 md:grid-cols-3">
			<div class="rounded border border-gray-200 bg-white p-4">
				<p class="text-sm text-gray-500">{$_('dashboard.totalVehicles')}</p>
				<p class="text-3xl font-bold">{stats.total_vehicles}</p>
			</div>
			<div class="rounded border border-gray-200 bg-white p-4">
				<p class="text-sm text-gray-500">{$_('dashboard.todayAccesses')}</p>
				<p class="text-3xl font-bold">{stats.today_access_total}</p>
			</div>
			<div class="rounded border border-gray-200 bg-white p-4">
				<p class="text-sm text-gray-500">{$_('dashboard.todayDenied')}</p>
				<p class="text-3xl font-bold text-red-600">{stats.today_denied_total}</p>
			</div>
			<div class="rounded border border-gray-200 bg-white p-4">
				<p class="text-sm text-gray-500">{$_('dashboard.activeSubscriptions')}</p>
				<p class="text-3xl font-bold text-green-600">{stats.active_subscriptions}</p>
			</div>
			<div class="rounded border border-gray-200 bg-white p-4">
				<p class="text-sm text-gray-500">{$_('dashboard.expiringSoon')}</p>
				<p class="text-3xl font-bold text-amber-500">{stats.expiring_soon_count}</p>
			</div>
		</div>
	{/if}

	<LiveTicker />
	<CameraFeed />
</div>
