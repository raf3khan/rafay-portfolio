# rafkhan.com

Personal portfolio of Rafay Khan. A single static page (`index.html`) served by GitHub Pages at [rafkhan.com](https://rafkhan.com).

## Security

- Every page carries the same Content-Security-Policy `<meta>` right after the viewport tag. Copy it into any new page under `/labs/`. It only allows scripts from this site and Google Analytics, styles and fonts from Google Fonts, and data requests to this site and Google Analytics. If a new tool needs another host, add it to the policy on that page.
- Third-party libraries are copied into `/vendor/` instead of loaded from a CDN. `vendor/lenis.min.js` is Lenis 1.1.13, taken from the npm package (checked against npm's integrity hash).
- Put text from data files on the page with `textContent`, or pass it through the page's `esc()` helper before using `innerHTML`.
