"""Temporary probe 2: pagination and Arabic names on Easy Sahm."""
import re, urllib.request, urllib.parse
UA = "Mozilla/5.0 (compatible; rafkhan-dividend-calendar/1.0; +https://rafkhan.com/labs/tadawul-dividends/)"
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status, r.read().decode("utf-8", "replace")
    except Exception as e: return getattr(e, "code", 0), str(e)
def flat(h):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    t = re.sub(r"<[^>]+>", "|", t)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"(\s*\|\s*)+", " | ", t)
    return t
c, h = get("https://easysahm.com/dividends")
print("PAGINATION LINKS:", sorted(set(re.findall(r'href="(/dividends\?[^"]+)"', h)))[:20])
i = h.find("Page 1 of"); print("PAGE CTX:", h[max(0,i-800):i+400] if i>=0 else "none")
for u in ["https://easysahm.com/dividends?page=2", "https://easysahm.com/dividends?p=2"]:
    c, h2 = get(u); m = re.search(r"Page \d+ of \d+", h2); print(u, c, m.group(0) if m else None)
    print(flat(h2)[flat(h2).find("Yield %"):][:600])
ar = "https://easysahm.com/ar/" + urllib.parse.quote("التقويم")
c, h3 = get(ar); print("AR", c, len(h3))
t = flat(h3); i = t.find("4333"); print("AR CTX:", t[max(0,i-200):i+1500])
t = flat(get("https://easysahm.com/calendar")[1]); i = t.find("Amount / share"); print("EN CAL:", t[i:i+2500])
c, h4 = get("https://easysahm.com/overview/4348"); t = flat(h4); i = t.find("Sector"); print("OVERVIEW", c, t[max(0,i-300):i+300])
