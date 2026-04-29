<script lang="ts">
  export const LICENSE_PLATE_REGEX = /^[A-Z0-9]{3,12}$/;

  let {
    onSubmit = (_payload: { license_plate: string }) => {}
  }: {
    onSubmit?: (payload: { license_plate: string }) => void;
  } = $props();

  let plate = $state('');
  let error = $state('');

  function validate(value: string): string | null {
    const normalized = value.replace(/\s+/g, '').toUpperCase();
    if (!LICENSE_PLATE_REGEX.test(normalized)) {
      return 'invalid';
    }
    return null;
  }

  function submitForm(event: SubmitEvent): void {
    event.preventDefault();
    const validationError = validate(plate);
    if (validationError) {
      error = validationError;
      return;
    }

    error = '';
    onSubmit({ license_plate: plate.replace(/\s+/g, '').toUpperCase() });
  }
</script>

<form onsubmit={submitForm}>
  <label>
    Plate
    <input aria-label="plate" bind:value={plate} />
  </label>
  {#if error}
    <p role="alert">Invalid plate</p>
  {/if}
  <button type="submit">Save</button>
</form>
