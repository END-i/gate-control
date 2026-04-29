<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onDestroy } from 'svelte';
	import { _ } from 'svelte-i18n';
	import { get } from 'svelte/store';

	import { api } from '$lib/api';
	import LanguageSwitcher from '$lib/components/LanguageSwitcher.svelte';
	import SystemStatusIndicator from '$lib/components/SystemStatusIndicator.svelte';
	import { setupI18n } from '$lib/i18n';
	import { authToken, clearAuthToken } from '$lib/stores/auth';

	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
	let triggerStateKey = $state('');

	setupI18n();

	const unsubscribe = authToken.subscribe((token) => {
		const pathname = get(page).url.pathname;
		if (!token && !pathname.startsWith('/login')) {
			goto('/login');
		}
	});

	onDestroy(() => {
		unsubscribe();
	});

	async function handleManualTrigger(): Promise<void> {
		triggerStateKey = '';
		try {
			await api.post('/relay/trigger');
			triggerStateKey = 'layout.gateOpened';
		} catch (error) {
			triggerStateKey = error instanceof Error ? error.message : 'layout.triggerFailed';
		}
	}

	function logout(): void {
		clearAuthToken();
		goto('/login');
	}
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

{#if $page.url.pathname.startsWith('/login')}
	{@render children()}
{:else}
	<div class="flex min-h-screen bg-gray-50">
		<aside class="w-64 border-r border-gray-200 bg-white p-4">
			<h2 class="mb-6 text-lg font-bold">{$_('layout.title')}</h2>
			<nav class="space-y-2">
				<a class="block rounded px-3 py-2 hover:bg-gray-100" href="/">{$_('layout.dashboard')}</a>
				<a class="block rounded px-3 py-2 hover:bg-gray-100" href="/vehicles">{$_('layout.vehicles')}</a>
				<a class="block rounded px-3 py-2 hover:bg-gray-100" href="/logs">{$_('layout.logs')}</a>
			</nav>
		</aside>

		<div class="flex min-h-screen flex-1 flex-col">
			<header class="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
				<div>
					<p class="text-sm text-gray-500">{$_('layout.subtitle')}</p>
					{#if triggerStateKey}
						<p class="text-sm">{$_(triggerStateKey)}</p>
					{/if}
				</div>
				<div class="flex items-center gap-2">
					<SystemStatusIndicator />
					<LanguageSwitcher />
					<button
						type="button"
						class="rounded bg-black px-4 py-2 text-sm font-semibold text-white"
						onclick={handleManualTrigger}
					>
						{$_('layout.manualTrigger')}
					</button>
					<button
						type="button"
						class="rounded border border-gray-300 px-4 py-2 text-sm font-semibold"
						onclick={logout}
					>
						{$_('common.logout')}
					</button>
				</div>
			</header>

			<main class="flex-1 p-6">
				{@render children()}
			</main>
		</div>
	</div>
{/if}
