/**
 * i18n.js — BharatPrice Pulse
 * Client-side internationalization system. Loads local JSON dictionaries.
 * Zero external network calls. Offline and Docker reproducible.
 */

class I18nManager {
  constructor() {
    this.currentLang = localStorage.getItem('bpp_lang') || 'en';
    this.translations = {};
    this.fallbackTranslations = {};
  }

  async init() {
    // Always load English as fallback
    try {
      const respEn = await fetch('/static/i18n/en.json');
      this.fallbackTranslations = await respEn.json();
    } catch (e) {
      console.warn('Could not load fallback en.json', e);
    }

    if (this.currentLang !== 'en') {
      await this.loadLanguage(this.currentLang);
    } else {
      this.translations = this.fallbackTranslations;
    }

    this.applyTranslations();
  }

  async loadLanguage(lang) {
    try {
      const resp = await fetch(`/static/i18n/${lang}.json`);
      if (resp.ok) {
        this.translations = await resp.json();
        this.currentLang = lang;
        localStorage.setItem('bpp_lang', lang);
      } else {
        console.warn(`Could not load ${lang}.json; falling back to English`);
        this.translations = this.fallbackTranslations;
        this.currentLang = 'en';
      }
    } catch (e) {
      console.error(`Failed to load translations for ${lang}`, e);
      this.translations = this.fallbackTranslations;
    }
    this.applyTranslations();
  }

  t(keyPath, defaultVal = '') {
    const keys = keyPath.split('.');
    let val = this.translations;
    for (const k of keys) {
      if (val && typeof val === 'object' && k in val) {
        val = val[k];
      } else {
        val = null;
        break;
      }
    }

    if (val !== null && val !== undefined) return val;

    // Check fallback
    let fbVal = this.fallbackTranslations;
    for (const k of keys) {
      if (fbVal && typeof fbVal === 'object' && k in fbVal) {
        fbVal = fbVal[k];
      } else {
        fbVal = null;
        break;
      }
    }
    return fbVal !== null && fbVal !== undefined ? fbVal : (defaultVal || '');
  }

  applyTranslations() {
    // 1. Text content
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const text = this.t(key, el.textContent || '');
      if (text) el.textContent = text;
    });

    // 2. Placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const text = this.t(key, el.getAttribute('placeholder') || '');
      if (text) el.setAttribute('placeholder', text);
    });

    // 3. Titles / tooltips
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      const text = this.t(key, el.getAttribute('title') || '');
      if (text) el.setAttribute('title', text);
    });

    // Update select element if present
    const select = document.getElementById('lang-select');
    if (select) {
      select.value = this.currentLang;
    }
  }
}

window.i18n = new I18nManager();
