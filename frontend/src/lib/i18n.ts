import { addMessages, getLocaleFromNavigator, init, locale } from 'svelte-i18n';

import bg from '../locales/bg.json';
import en from '../locales/en.json';
import ru from '../locales/ru.json';
import uk from '../locales/uk.json';

const STORAGE_KEY = 'anpr_locale';
const FALLBACK_LOCALE = 'en';

addMessages('en', en);
addMessages('ru', ru);
addMessages('uk', uk);
addMessages('bg', bg);

function resolveInitialLocale(): string {
  if (typeof window === 'undefined') {
    return FALLBACK_LOCALE;
  }

  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && ['en', 'ru', 'uk', 'bg'].includes(stored)) {
    return stored;
  }

  const fromNavigator = getLocaleFromNavigator();
  if (fromNavigator && ['en', 'ru', 'uk', 'bg'].includes(fromNavigator.slice(0, 2))) {
    return fromNavigator.slice(0, 2);
  }

  return FALLBACK_LOCALE;
}

export function setupI18n(): void {
  init({
    fallbackLocale: FALLBACK_LOCALE,
    initialLocale: resolveInitialLocale()
  });
}

export function setLocale(nextLocale: 'en' | 'ru' | 'uk' | 'bg'): void {
  locale.set(nextLocale);
  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, nextLocale);
  }
}
