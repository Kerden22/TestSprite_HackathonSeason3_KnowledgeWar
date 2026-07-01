let _dict = {};
let _lang = 'en';

const SUPPORTED_LANGS = ['en', 'tr'];
const LANG_STORAGE_KEY = 'lang';

function resolveLang(code) {
  return SUPPORTED_LANGS.includes(code) ? code : 'en';
}

function getLang() {
  return _lang;
}

function getLangFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get('lang');
  return fromUrl ? resolveLang(fromUrl.toLowerCase()) : null;
}

function getStoredLang() {
  const stored = localStorage.getItem(LANG_STORAGE_KEY);
  return stored ? resolveLang(stored) : 'en';
}

function t(key) {
  const parts = key.split('.');
  let node = _dict;
  for (const part of parts) {
    if (node == null || typeof node !== 'object') return key;
    node = node[part];
  }
  return typeof node === 'string' ? node : key;
}

function tFormat(key, vars = {}) {
  let str = t(key);
  Object.entries(vars).forEach(([k, v]) => {
    str = str.replaceAll(`{${k}}`, String(v));
  });
  return str;
}

async function loadDictionary(lang) {
  const response = await fetch(`/static/i18n/${lang}.json`);
  if (!response.ok) throw new Error(`Failed to load i18n/${lang}.json`);
  _dict = await response.json();
  _lang = lang;
  document.documentElement.lang = lang;
}

async function initI18n() {
  const fromUrl = getLangFromUrl();
  const lang = fromUrl || getStoredLang();
  if (fromUrl) localStorage.setItem(LANG_STORAGE_KEY, lang);
  await loadDictionary(lang);
  updateLangToggleUI();
}

function applyTranslations() {
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.getAttribute('data-i18n');
    if (key) el.textContent = t(key);
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (key) el.placeholder = t(key);
  });

  document.querySelectorAll('[data-i18n-aria]').forEach((el) => {
    const key = el.getAttribute('data-i18n-aria');
    if (key) el.setAttribute('aria-label', t(key));
  });

  document.querySelectorAll('[data-i18n-title]').forEach((el) => {
    const key = el.getAttribute('data-i18n-title');
    if (key) el.title = t(key);
  });

  const titleKey = document.body.getAttribute('data-i18n-page-title');
  if (titleKey) document.title = t(titleKey);
}

function setLang(code) {
  const lang = resolveLang(code);
  localStorage.setItem(LANG_STORAGE_KEY, lang);
  const url = new URL(window.location.href);
  url.searchParams.delete('lang');
  window.location.href = url.toString();
}

function updateLangToggleUI() {
  const enBtn = document.getElementById('langEn');
  const trBtn = document.getElementById('langTr');
  if (!enBtn || !trBtn) return;

  const active = 'text-cyan-400 font-bold';
  const inactive = 'text-gray-400 hover:text-white font-medium';

  enBtn.className = _lang === 'en' ? active : inactive;
  trBtn.className = _lang === 'tr' ? active : inactive;
}

function setupLangToggle() {
  const langToggle = document.getElementById('langToggle');
  if (langToggle) {
    langToggle.addEventListener('click', (e) => {
      const btn = e.target.closest('button');
      if (!btn) return;
      if (btn.id === 'langEn') setLang('en');
      if (btn.id === 'langTr') setLang('tr');
    });
    return;
  }
  const enBtn = document.getElementById('langEn');
  const trBtn = document.getElementById('langTr');
  if (enBtn) enBtn.addEventListener('click', () => setLang('en'));
  if (trBtn) trBtn.addEventListener('click', () => setLang('tr'));
}

document.addEventListener('DOMContentLoaded', () => {
  setupLangToggle();
});
