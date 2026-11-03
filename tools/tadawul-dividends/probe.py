"""Temporary probe: prints the structure of the free dividend sources so the parser can be written."""
import re, urllib.request, json, sys

UA = "Mozilla/5.0 (compatible; rafkhan-dividend-calendar/1.0; +https://rafkhan.com/labs/tadawul-dividends/)"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", 0), str(e)

for url in ["https://easysahm.com/calendar", "https://easysahm.com/dividends",
            "https://web.derayah.com/en/sa-stocks-dividend-eligibility-payments-nov-wk1-2026/",
            "https://stockanalysis.com/quote/tadawul/7010/dividend/"]:
    code, html = get(url)
    print("=" * 30, url, code, len(html))
    nd = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    print("NEXT_DATA:", bool(nd), len(nd.group(1)) if nd else 0)
    if nd:
        print(nd.group(1)[:3000])
    for m in re.finditer(r"<table.*?</table>", html, re.S):
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", m.group(0)))
        print("TABLE:", t[:1500])
    for kw in ["7010", "Alinma", "1150", "eligib", "dividend"]:
        i = html.find(kw)
        if i >= 0:
            print("KW", kw, "->", re.sub(r"\s+", " ", html[max(0, i - 300): i + 500]))
    scripts = re.findall(r"<script[^>]*src=\"([^\"]+)\"", html)
    print("SCRIPTS:", scripts[:15])
    apis = set(re.findall(r"https?://[a-zA-Z0-9.-]+/api/[^\"' ]+", html))
    print("APIS:", list(apis)[:20])
