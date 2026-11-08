/* Cookie consent + Google Analytics 4 for rafkhan.com and every Labs page.
   Add to a page's <head>: <script src="/analytics.js" defer></script>

   Google Analytics only loads after the visitor picks "Accept"; "Decline" keeps it off.
   The site sets no other optional cookies (tool settings stay in the visitor's own
   browser storage and are never sent anywhere).
   The choice is kept for 12 months in localStorage under "rk-consent".
   Anywhere on the site, window.rkConsent.open() shows the window again. */
(function () {
  var ID = 'G-C37NH6M8LT';
  var KEY = 'rk-consent';
  var VERSION = 1;
  var MAX_AGE = 365 * 24 * 60 * 60 * 1000;
  var LIVE = /(^|\.)rafkhan\.com$/.test(location.hostname); // previews and local files never load GA

  var TEXT = {
    en: {
      label: 'Cookie consent',
      body: 'Can I use analytics cookies to see which tools people use?',
      policy: 'Privacy policy',
      all: 'Accept',
      reject: 'Decline',
      footer: 'Privacy and cookies'
    },
    ar: {
      label: 'الموافقة على ملفات تعريف الارتباط',
      body: 'هل تسمح باستخدام ملفات تعريف ارتباط التحليلات لمعرفة الأدوات التي يستخدمها الزوار؟',
      policy: 'سياسة الخصوصية',
      all: 'قبول',
      reject: 'رفض',
      footer: 'الخصوصية وملفات تعريف الارتباط'
    }
  };
  function lang() { return /^ar/i.test(document.documentElement.lang || '') ? 'ar' : 'en'; }
  function T() { return TEXT[lang()]; }

  // ---------- stored choice ----------
  function read() {
    try {
      var c = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (c && c.v === VERSION && Date.now() - c.t < MAX_AGE) return c.choice;
    } catch (e) {}
    return null;
  }
  var sessionChoice = null; // used when browser storage is blocked
  function save(choice) {
    sessionChoice = choice;
    try { localStorage.setItem(KEY, JSON.stringify({ v: VERSION, choice: choice, t: Date.now() })); } catch (e) {}
  }
  function current() { return read() || sessionChoice; }

  // ---------- Google Analytics ----------
  var loaded = false;
  function loadGA() {
    window['ga-disable-' + ID] = false;
    if (loaded || !LIVE) return;
    loaded = true;
    var s = document.createElement('script'); s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag('js', new Date());
    gtag('config', ID);
  }
  function stopGA() {
    window['ga-disable-' + ID] = true;
    // remove any _ga cookies left from an earlier "Yes"
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (!/^_ga/.test(name)) return;
      ['', '; domain=' + location.hostname, '; domain=.' + location.hostname.replace(/^www\./, '')].forEach(function (d) {
        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + d;
      });
    });
  }

  // which lab tool people open from the portfolio
  document.addEventListener('click', function (e) {
    if (!loaded || !window.gtag) return;
    var a = e.target.closest && e.target.closest('a.lab');
    if (!a) return;
    var h = a.querySelector('h3');
    gtag('event', 'lab_open', { tool: h ? h.textContent.trim() : a.getAttribute('href'), link_url: a.href });
  });

  // ---------- consent window ----------
  var CSS =
    '.rkc{position:fixed;right:16px;bottom:16px;z-index:1000;width:min(280px,calc(100vw - 32px));padding:12px;display:grid;gap:10px;' +
    'background:var(--surface,#fff);color:var(--ink,#111);border:1px solid var(--line,#dcdcd8);border-radius:16px;' +
    'box-shadow:0 2px 4px rgba(0,0,0,.08),0 12px 32px rgba(0,0,0,.14);border-radius:12px;font:400 13px/18px var(--font,system-ui,sans-serif)}' +
    '.rkc[dir="rtl"]{font-family:var(--arabic,system-ui,sans-serif)}' +
    '.rkc p{margin:0;color:var(--muted,#565656)}' +
    '.rkc p a{color:var(--accent,#1f7d37);text-underline-offset:3px}' +
    '.rkc .rkc-b{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}' +
    '.rkc button{min-width:0;min-height:32px;padding:4px 8px;border-radius:8px;cursor:pointer;font-size:13px;line-height:16px;font-weight:500;font-family:inherit;' +
    'border:1px solid var(--line,#dcdcd8);background:var(--surface,#fff);color:var(--ink,#111)}' +
    '.rkc button:hover{border-color:var(--muted,#565656)}' +
    '.rkc button:focus-visible{outline:2px solid var(--accent,#1f7d37);outline-offset:2px}' +
    '@media (max-width:480px){.rkc{right:8px;bottom:8px;width:min(280px,calc(100vw - 16px))}}' +
    '@media (prefers-reduced-motion:no-preference){.rkc{animation:rkc-in .3s cubic-bezier(.22,1,.36,1)}}' +
    '@keyframes rkc-in{from{opacity:0;transform:translateY(8px)}}' +
    '@media print{.rkc{display:none}}';

  var box = null;
  function policyHref() { return '/privacy/' + (lang() === 'ar' ? '?lang=ar' : ''); }
  function fill() {
    if (!box) return;
    var t = T();
    box.lang = lang(); box.dir = lang() === 'ar' ? 'rtl' : 'ltr';
    box.setAttribute('aria-label', t.label);
    var p = box.querySelector('p');
    p.textContent = t.body + ' ';
    var a = document.createElement('a'); a.href = policyHref(); a.textContent = t.policy; p.appendChild(a);
    var b = box.querySelectorAll('button');
    b[0].textContent = t.all; b[1].textContent = t.reject;
  }
  function choose(choice) {
    save(choice);
    if (choice === 'all') loadGA(); else stopGA();
    close();
    document.dispatchEvent(new CustomEvent('rk-consent', { detail: choice }));
  }
  function open() {
    if (box) { box.querySelector('button').focus(); return; }
    if (!document.getElementById('rkc-css')) {
      var st = document.createElement('style'); st.id = 'rkc-css'; st.textContent = CSS; document.head.appendChild(st);
    }
    box = document.createElement('section');
    box.className = 'rkc';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-label', T().label);
    box.innerHTML = '<p></p><div class="rkc-b">' +
      '<button type="button" data-c="all"></button><button type="button" data-c="reject"></button></div>';
    box.addEventListener('click', function (e) {
      var c = e.target.closest('button[data-c]');
      if (c) choose(c.getAttribute('data-c'));
    });
    fill();
    document.body.appendChild(box);
  }
  function close() { if (box) { box.remove(); box = null; } }

  // footer link to the privacy page, in the page's language
  function footerLink() {
    var col = document.querySelector('footer .col, .fine .col');
    if (!col || col.querySelector('.rkc-link') || location.pathname.indexOf('/privacy') === 0) return;
    var a = document.createElement('a'); a.className = 'rkc-link'; a.href = policyHref(); a.textContent = T().footer;
    var last = col.lastElementChild;
    if (last && last.tagName === 'A') {
      var wrap = document.createElement('span'); wrap.style.cssText = 'display:inline-flex;gap:16px;flex-wrap:wrap';
      col.insertBefore(wrap, last); wrap.appendChild(a); wrap.appendChild(last);
    } else col.appendChild(a);
  }

  // Bilingual pages switch <html lang> without reloading, so follow it.
  new MutationObserver(function () {
    fill();
    var l = document.querySelector('.rkc-link');
    if (l) { l.textContent = T().footer; l.href = policyHref(); }
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });

  window.rkConsent = { open: open, get: current, choose: choose };

  function boot() {
    footerLink();
    var c = current();
    if (c === 'all') loadGA();
    else if (!c) open();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
