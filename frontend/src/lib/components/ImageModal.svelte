<script lang="ts">
  import { _ } from 'svelte-i18n';

  let {
    open = false,
    imageUrl = '',
    onClose = () => {}
  }: {
    open?: boolean;
    imageUrl?: string;
    onClose?: () => void;
  } = $props();
</script>

{#if open}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
    <button type="button" class="absolute inset-0" aria-label={$_('imageModal.closeLabel')} onclick={onClose}></button>
    <div role="dialog" aria-modal="true" class="relative max-h-[90vh] w-full max-w-4xl overflow-hidden rounded bg-white p-2">
      <div class="mb-2 flex justify-end">
        <button class="rounded border border-gray-300 px-3 py-1" onclick={onClose}>{$_('imageModal.close')}</button>
      </div>
      <img class="max-h-[80vh] w-full object-contain" src={imageUrl} alt={$_('imageModal.alt')} />
    </div>
  </div>
{/if}
