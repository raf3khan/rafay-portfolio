"""Builds sitemap.xml from every index.html in the repo.

Rules, so new Labs tools are picked up with no extra work:
- Every index.html becomes https://rafkhan.com/<folder>/ unless it has <meta name="robots" content="noindex">.
- A page that lists <link rel="alternate" hreflang="..."> gets one sitemap entry per language,
  each carrying all the alternates, which is how Google pairs the English and Arabic versions.
- lastmod is the date of the last git commit that touched the page or its data folder.
Run by .github/workflows/sitemap.yml on every push to main. Standard library only.
"""
import pathlib, re, subprocess, html

ROOT = pathlib.Path(__file__).resolve().parents[2]
SITE = "https://rafkhan.com/"
SKIP = {"node_modules", ".git", "tools", "og"}


def lastmod(folder: pathlib.Path) -> str:
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(folder.relative_to(ROOT) or ".")],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return out


def pages():
    for f in sorted(ROOT.rglob("index.html")):
        rel = f.relative_to(ROOT)
        if SKIP & set(rel.parts):
            continue
        src = f.read_text(encoding="utf-8", errors="ignore")
        head = src.split("</head>", 1)[0]
        if re.search(r'<meta[^>]+name="robots"[^>]+noindex', head, re.I):
            continue
        url = SITE + "/".join(rel.parts[:-1]) + ("/" if len(rel.parts) > 1 else "")
        alts = re.findall(r'<link[^>]+rel="alternate"[^>]+hreflang="([^"]+)"[^>]+href="([^"]+)"', head)
        # The home page's lastmod follows index.html only, not the whole repo.
        mod = lastmod(f if len(rel.parts) == 1 else f.parent)
        yield url, alts, mod


def main():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for url, alts, mod in pages():
        locs = [h for l, h in alts if l != "x-default"] or [url]
        for loc in dict.fromkeys(locs):
            lines.append("  <url>")
            lines.append("    <loc>%s</loc>" % html.escape(loc))
            if mod:
                lines.append("    <lastmod>%s</lastmod>" % mod)
            for l, h in alts:
                lines.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (l, html.escape(h)))
            lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
