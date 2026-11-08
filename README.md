# rafkhan.com

Personal portfolio of Rafay Khan. A single static page (`index.html`) served by GitHub Pages at [rafkhan.com](https://rafkhan.com).

## Security

- Every page carries the same Content-Security-Policy `<meta>` right after the viewport tag. Copy it into any new page under `/labs/`. It only allows scripts from this site and Google Analytics, styles and fonts from this site, and data requests to this site and Google Analytics. If a new tool needs another host, add it to the policy on that page.
- Fonts are self-hosted in `/fonts/` (`fonts.css` plus woff2 files, OFL licensed). New pages link `/fonts/fonts.css` instead of Google Fonts. To add a weight or family, download it from Google Fonts (latin, latin-ext, arabic subsets) into `/fonts/` and add its `@font-face` to `fonts.css`.
- Third-party libraries are copied into `/vendor/` instead of loaded from a CDN. `vendor/lenis.min.js` is Lenis 1.1.13, taken from the npm package (checked against npm's integrity hash).
- `analytics.js` is also the cookie consent window. Google Analytics only loads after a visitor picks "Accept"; "Decline" keeps it off. The choice is kept for 12 months. It adds a "Privacy and cookies" link to the page footer (`footer .col` or `.fine .col`), so new pages get it by including the script and a footer. The policy itself is `/privacy/` (EN and AR). If a page ever adds another cookie or tracker, update the policy and bump `VERSION` in `analytics.js` so everyone is asked again.
- Put text from data files on the page with `textContent`, or pass it through the page's `esc()` helper before using `innerHTML`.
