import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';

import VehicleForm from '$lib/components/VehicleForm.svelte';

describe('VehicleForm', () => {
  it('shows validation error for invalid plate', async () => {
    render(VehicleForm);

    const input = screen.getByLabelText('plate');
    await fireEvent.input(input, { target: { value: 'ab' } });
    await fireEvent.submit(screen.getByRole('button', { name: 'Save' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Invalid plate');
  });

  it('dispatches normalized plate for valid input', async () => {
    const handleSubmit = vi.fn();
    render(VehicleForm, { onSubmit: handleSubmit });

    const input = screen.getByLabelText('plate');
    await fireEvent.input(input, { target: { value: 'ab 1234 cd' } });
    await fireEvent.submit(screen.getByRole('button', { name: 'Save' }));

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    expect(handleSubmit.mock.calls[0][0]).toEqual({ license_plate: 'AB1234CD' });
  });
});
