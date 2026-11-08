# SEO checklist for a Labs page

Every page at `rafkhan.com/labs/<tool>/` should have the items below in its `<head>`.
`labs/tadawul-dividends/index.html` is the worked example: copy from it.

## 1. Title and description (the search result snippet)
- `<title>`: lead with what people search for, then a short benefit. About 50 to 60 characters.
  Example: `Saudi Broker Fee Calculator: the real cost of a Tadawul trade`.
- `<meta name="description">`: 140 to 160 characters, plain words, say it is free and in which languages.
- Arabic pages: also set `docTitle` and `docDesc` in the Arabic strings and update both in `applyLang()`
  (`document.title = t.docTitle;` and the `meta[name="description"]` content).

## 2. Canonical
- English-only page: `<link rel="canonical" href="https://rafkhan.com/labs/<tool>/">` (with the trailing slash).
- Bilingual page using `?lang=ar`: do not put a canonical in the HTML. Use the small head script from the
  dividend calendar, which sets the canonical to `/labs/<tool>/` or `/labs/<tool>/?lang=ar`.

## 3. hreflang (bilingual pages only)
```html
<link rel="alternate" hreflang="en" href="https://rafkhan.com/labs/<tool>/">
<link rel="alternate" hreflang="ar" href="https://rafkhan.com/labs/<tool>/?lang=ar">
<link rel="alternate" hreflang="x-default" href="https://rafkhan.com/labs/<tool>/">
```
The language button should also write `?lang=` into the address bar (see the dividend calendar's
`langBtn` handler), so a shared link opens in the language the sender saw.

## 4. Open Graph (link previews in WhatsApp, LinkedIn, X)
`og:type`, `og:site_name` (Rafay Khan), `og:title`, `og:description`, `og:url`,
`og:image` = `https://rafkhan.com/og/<tool>.png` with width 1200 and height 630, `og:image:alt`,
`og:locale` (plus `og:locale:alternate` = `ar_SA` if bilingual), and `twitter:card` = `summary_large_image`.

Make the image: add an entry for `<tool>` to `tools/seo/og-cards.json`, run `node tools/seo/make-og.js`,
commit `og/<tool>.png`.

## 5. Structured data (JSON-LD)
One `<script type="application/ld+json">` with:
- `WebApplication`: name, alternateName (Arabic name), url, description, `applicationCategory: FinanceApplication`,
  `operatingSystem: Any`, `inLanguage`, `isAccessibleForFree: true`, `offers` price 0, `author` Rafay Khan.
- `BreadcrumbList`: Rafay Khan > Labs > the tool.
- `FAQPage` only if the same questions and answers are visible on the page. Google shows FAQ rich results only
  for a few sites now, but answer engines still read them.

## 6. On-page content
- One `<h1>` with the main search phrase. Real `<h2>` sections.
- A short "how it works" or method section in plain text (100 to 300 words), with the data source and date.
  Calculators with no text rank poorly.
- Link back to `/#labs`, and link to one or two related tools.

## 7. Sitemap and robots
Nothing to do. `.github/workflows/sitemap.yml` rebuilds `sitemap.xml` from every `index.html` on each push
to main, and reads the hreflang links for the Arabic URL. Pages with `<meta name="robots" content="noindex">`
are left out.

## 8. Analytics
Load the shared Google Analytics file on every page: `<script src="/analytics.js" defer></script>` in the `<head>`.
Do not paste the GA snippet or measurement ID into the page; `/analytics.js` holds it.

## 9. Do not
- Publish a personal email or phone number anywhere, including JSON-LD. LinkedIn only.
- Use `?lang=` values other than `en` and `ar`.
