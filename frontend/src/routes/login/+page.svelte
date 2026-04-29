<script lang="ts">
  import { goto } from '$app/navigation';
  import { _ } from 'svelte-i18n';

  import { api } from '$lib/api';
  import { authToken, setAuthToken } from '$lib/stores/auth';

  type LoginResponse = {
    access_token: string;
    token_type: string;
  };

  let username = $state('');
  let password = $state('');
  let loading = $state(false);
  let errorMessage = $state('');

  $effect(() => {
    if ($authToken) {
      goto('/');
    }
  });

  async function submitLogin(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    loading = true;
    errorMessage = '';

    try {
      const payload = await api.post<LoginResponse>('/auth/login', { username, password }, { skipAuth: true });
      setAuthToken(payload.access_token);
      await goto('/');
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'login.failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="mx-auto max-w-md p-6">
  <h1 class="mb-4 text-2xl font-bold">{$_('login.title')}</h1>
  <form class="space-y-4" onsubmit={submitLogin}>
    <label class="block">
      <span class="mb-1 block text-sm">{$_('login.username')}</span>
      <input
        class="w-full rounded border border-gray-300 px-3 py-2"
        type="text"
        bind:value={username}
        autocomplete="username"
        required
      />
    </label>

    <label class="block">
      <span class="mb-1 block text-sm">{$_('login.password')}</span>
      <input
        class="w-full rounded border border-gray-300 px-3 py-2"
        type="password"
        bind:value={password}
        autocomplete="current-password"
        required
      />
    </label>

    {#if errorMessage}
      <p class="text-sm text-red-600">{$_(errorMessage)}</p>
    {/if}

    <button
      class="w-full rounded bg-black px-4 py-2 font-semibold text-white disabled:opacity-60"
      type="submit"
      disabled={loading}
    >
      {#if loading}{$_('login.signingIn')}{:else}{$_('login.signIn')}{/if}
    </button>
  </form>
</div>
