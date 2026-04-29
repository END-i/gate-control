import { fireEvent, render, screen } from '@testing-library/svelte';
import { get } from 'svelte/store';
import { describe, expect, it } from 'vitest';
import { locale } from 'svelte-i18n';

import LanguageSwitcher from '$lib/components/LanguageSwitcher.svelte';
import { setupI18n } from '$lib/i18n';

describe('LanguageSwitcher', () => {
  it('changes locale and persists to localStorage', async () => {
    setupI18n();
    render(LanguageSwitcher);

    const select = screen.getByRole('combobox');
    await fireEvent.change(select, { target: { value: 'uk' } });

    expect(get(locale)).toBe('uk');
    expect(localStorage.getItem('anpr_locale')).toBe('uk');
  });
});
