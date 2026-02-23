(function () {
  'use strict';

  var LANGS = [
    ['en', 'English'],
    ['es', 'Español'],
    ['fr', 'Français'],
    ['de', 'Deutsch'],
    ['pt', 'Português'],
    ['it', 'Italiano'],
    ['nl', 'Nederlands'],
    ['pl', 'Polski'],
    ['ru', 'Русский'],
    ['uk', 'Українська'],
    ['tr', 'Türkçe'],
    ['ar', 'العربية'],
    ['hi', 'हिन्दी'],
    ['zh-CN', '中文(简体)'],
    ['zh-TW', '中文(繁體)'],
    ['ja', '日本語'],
    ['ko', '한국어'],
    ['vi', 'Tiếng Việt'],
    ['th', 'ไทย'],
    ['id', 'Bahasa Indonesia']
  ];

  var RTL = { ar: true };
  var KEY = 'duovox-lang';
  var cache = {};

  function buildSelector() {
    var nav = document.querySelector('.nav-inner');
    if (!nav) return null;

    var wrap = document.createElement('div');
    wrap.className = 'lang-wrap';
    wrap.innerHTML = '<span class="lang-icon">&#127760;</span>';

    var sel = document.createElement('select');
    sel.className = 'lang-select';
    sel.setAttribute('aria-label', 'Language');

    LANGS.forEach(function (l) {
      var o = document.createElement('option');
      o.value = l[0];
      o.textContent = l[1];
      sel.appendChild(o);
    });

    wrap.appendChild(sel);
    nav.appendChild(wrap);
    return sel;
  }

  function apply(t) {
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var k = el.getAttribute('data-i18n');
      if (!el.hasAttribute('data-t')) el.setAttribute('data-t', el.textContent);
      if (t[k] != null) el.textContent = t[k];
    });
    document.querySelectorAll('[data-i18n-html]').forEach(function (el) {
      var k = el.getAttribute('data-i18n-html');
      if (!el.hasAttribute('data-t')) el.setAttribute('data-t', el.innerHTML);
      if (t[k] != null) el.innerHTML = t[k];
    });
  }

  function restore() {
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var d = el.getAttribute('data-t');
      if (d != null) el.textContent = d;
    });
    document.querySelectorAll('[data-i18n-html]').forEach(function (el) {
      var d = el.getAttribute('data-t');
      if (d != null) el.innerHTML = d;
    });
  }

  function setLang(code) {
    localStorage.setItem(KEY, code);
    document.documentElement.lang = code;
    document.documentElement.dir = RTL[code] ? 'rtl' : 'ltr';

    if (code === 'en') { restore(); return; }
    if (cache[code]) { apply(cache[code]); return; }

    fetch('lang/' + code + '.json')
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (j) { cache[code] = j; apply(j); })
      .catch(function (e) { console.warn('i18n: ' + code, e); });
  }

  function init() {
    var sel = buildSelector();
    if (!sel) return;

    var saved = localStorage.getItem(KEY);
    var lang = (saved && LANGS.some(function (l) { return l[0] === saved; })) ? saved : 'en';
    sel.value = lang;
    sel.addEventListener('change', function () { setLang(this.value); });
    if (lang !== 'en') setLang(lang);
  }

  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', init);
  else init();
})();
