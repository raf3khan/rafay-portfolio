/* Google Analytics 4 for rafkhan.com and every Labs page.
   Add to a page's <head>: <script src="/analytics.js" defer></script> */
(function () {
  var ID = 'G-C37NH6M8LT';
  if (!/(^|\.)rafkhan\.com$/.test(location.hostname)) return; // skip previews and local files
  var s = document.createElement('script'); s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + ID;
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { dataLayer.push(arguments); };
  gtag('js', new Date());
  gtag('config', ID);
  // which lab tool people open from the portfolio
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a.lab');
    if (!a) return;
    var h = a.querySelector('h3');
    gtag('event', 'lab_open', { tool: h ? h.textContent.trim() : a.getAttribute('href'), link_url: a.href });
  });
})();
