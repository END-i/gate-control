<script lang="ts">
  import { locale } from 'svelte-i18n';

  import { setLocale } from '$lib/i18n';

  let current = $state('en');

  const unsubscribe = locale.subscribe((value) => {
    current = value ?? 'en';
  });

  function handleChange(event: Event): void {
    const target = event.currentTarget as HTMLSelectElement;
    const value = target.value as 'en' | 'ru' | 'uk' | 'bg';
    setLocale(value);
  }

  $effect(() => {
    return () => unsubscribe();
  });
</script>

<select class="rounded border border-gray-300 px-2 py-2 text-sm" value={current} onchange={handleChange}>
  <option value="en">EN</option>
  <option value="ru">RU</option>
  <option value="uk">UK</option>
  <option value="bg">BG</option>
</select>
