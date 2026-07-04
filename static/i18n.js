// Apply theme immediately to documentElement to avoid styling flash
(function() {
  const theme = localStorage.getItem('theme') || 'dark';
  document.documentElement.classList.add(theme);
  document.documentElement.classList.remove(theme === 'dark' ? 'light' : 'dark');
})();

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

  // Update theme button title dynamically with active language
  const themeBtn = document.getElementById('themeToggleBtn');
  if (themeBtn) {
    const isDark = document.documentElement.classList.contains('dark');
    const isTr = _lang === 'tr';
    themeBtn.title = isDark
      ? (isTr ? 'Açık Temaya Geç' : 'Switch to Light Mode')
      : (isTr ? 'Koyu Temaya Geç' : 'Switch to Dark Mode');
  }
}

function setLang(code) {
  const lang = resolveLang(code);
  localStorage.setItem(LANG_STORAGE_KEY, lang);
  const url = new URL(window.location.href);
  url.searchParams.delete('lang');
  const target = url.toString();
  // If the target only differs by (or shares) a hash fragment, assigning
  // location.href won't reload the page — force a reload so the new locale
  // is actually applied. Otherwise navigate normally (e.g. dropping ?lang=).
  if (target === window.location.href || target.split('#')[0] === window.location.href.split('#')[0]) {
    window.location.reload();
  } else {
    window.location.href = target;
  }
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

function setupThemeToggle() {
  const currentTheme = localStorage.getItem('theme') || 'dark';
  // Also apply to body when body is ready
  document.body.classList.add(currentTheme);
  document.body.classList.remove(currentTheme === 'dark' ? 'light' : 'dark');

  const langToggle = document.getElementById('langToggle');
  let parentNode = langToggle || document.getElementById('langEn')?.parentNode;
  
  if (!parentNode) {
    // Fallback for pages like battle screen which might not have a lang toggle but have the navigation area
    parentNode = document.querySelector('.timer')?.parentNode || document.querySelector('.nav-right') || document.querySelector('header');
  }

  if (parentNode) {
    // Check if the theme toggle button already exists to prevent duplicate injections
    if (document.getElementById('themeToggleBtn')) return;

    const themeBtn = document.createElement('button');
    themeBtn.type = 'button';
    themeBtn.id = 'themeToggleBtn';
    
    // Style the button matching the rest of the navigation
    themeBtn.className = 'ml-3 p-1.5 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-white transition-colors cursor-pointer flex items-center justify-center text-base';
    themeBtn.style.outline = 'none';
    
    const isTr = _lang === 'tr';
    themeBtn.innerHTML = currentTheme === 'dark' ? '☀️' : '🌙';
    themeBtn.title = currentTheme === 'dark' 
      ? (isTr ? 'Açık Temaya Geç' : 'Switch to Light Mode') 
      : (isTr ? 'Koyu Temaya Geç' : 'Switch to Dark Mode');

    themeBtn.addEventListener('click', () => {
      const isDark = document.documentElement.classList.contains('dark');
      if (isDark) {
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
        document.body.classList.remove('dark');
        document.body.classList.add('light');
        localStorage.setItem('theme', 'light');
        themeBtn.innerHTML = '🌙';
        themeBtn.title = isTr ? 'Koyu Temaya Geç' : 'Switch to Dark Mode';
      } else {
        document.documentElement.classList.remove('light');
        document.documentElement.classList.add('dark');
        document.body.classList.remove('light');
        document.body.classList.add('dark');
        localStorage.setItem('theme', 'dark');
        themeBtn.innerHTML = '☀️';
        themeBtn.title = isTr ? 'Açık Temaya Geç' : 'Switch to Light Mode';
      }
    });

    parentNode.appendChild(themeBtn);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  setupLangToggle();
  setupThemeToggle();
});
