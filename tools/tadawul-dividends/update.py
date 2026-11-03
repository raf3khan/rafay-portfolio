"""Refresh labs/tadawul-dividends/data/dividends.json from Easy Sahm's free public pages.

Runs in GitHub Actions (no API keys, no Claude). Sources:
  * easysahm.com/calendar      announced Saudi dividends: amount, eligibility date, pay date (about two weeks ahead)
  * easysahm.com/ar/التقويم    the same list with Arabic company names
  * easysahm.com/dividends     every Saudi dividend payer: next announced eligibility, 12-month total and yield

Rules: never delete what a person or Claude entered by hand except events that are long past, never overwrite an
existing name, nameAr, sector or period, and stop with an error (writing nothing) if the pages stop parsing.
"""
import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "labs" / "tadawul-dividends" / "data" / "dividends.json"
UA = "Mozilla/5.0 (compatible; rafkhan-dividend-calendar/1.0; +https://rafkhan.com/labs/tadawul-dividends/)"
KEEP_DAYS = 45
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
DATE = r"\d{1,2} [A-Za-z]{3,9} \d{4}"


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # network hiccup: retry with backoff
            print(f"fetch failed ({i + 1}/{tries}) {url}: {e}", file=sys.stderr)
            time.sleep(2 ** (i + 1))
    raise RuntimeError(f"could not fetch {url}")


def flat(html):
    """Visible text with every tag boundary turned into a single ' | ' separator."""
    t = re.sub(r"<(script|style|template)[^>]*>.*?</\1>", " ", html, flags=re.S)
    t = re.sub(r"<[^>]+>", "|", t)
    t = t.replace("&amp;", "&").replace("&#x27;", "'").replace("&quot;", '"').replace("&nbsp;", " ")
    t = re.sub(r"\s+", " ", t)
    return re.sub(r"(\s*\|\s*)+", " | ", t)


def iso(s):
    d, m, y = s.split()
    return dt.date(int(y), MONTHS[m[:3].lower()], int(d)).isoformat()


def parse_calendar(text):
    if "Amount / share" not in text:
        raise RuntimeError("calendar page layout changed: dividend table header not found")
    rows = []
    pat = re.compile(r"\| (\d{4}) \| KSA \| ([^|]+?) \| SAR ([\d.]+) \| (" + DATE + r") \| Eligibility date \|(.*?)(?=\| (?:\d{4}|[A-Z.]{1,6}) \| (?:KSA|US) \||$)")
    for m in pat.finditer(text):
        pay = re.search(r"pays \| (" + DATE + ")", m.group(5))
        rows.append({"ticker": m.group(1), "name": m.group(2).strip(), "dps": float(m.group(3)),
                     "recordDate": iso(m.group(4)), "payDate": iso(pay.group(1)) if pay else None})
    return rows


def parse_calendar_ar(text):
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"\| (\d{4}) \| السعودي \| ([^|]+?) \| [\d.]+ ر\.س \|", text)}


def parse_payers(text):
    out = {}
    pat = re.compile(r"\| (\d{4}) \| ([^|]+?) \| \( \| \1 \| \) \| Last dividend \|(.*?)\| ([\d.]+)% \| Last 12 months")
    for m in pat.finditer(text):
        body = m.group(3)
        nxt = re.search(r"Next eligibility \| : \| (" + DATE + r") \| SAR ([\d.]+)", body)
        ttm = re.search(r"12-month total \| : \| SAR ([\d.]+)", body)
        yld = float(m.group(4))
        rec = {"name": m.group(2).strip()}
        if ttm and yld > 0:
            rec["annualDps"] = float(ttm.group(1))
            rec["price"] = round(float(ttm.group(1)) / (yld / 100), 2)
        if nxt:
            rec["next"] = {"recordDate": iso(nxt.group(1)), "dps": float(nxt.group(2))}
        out[m.group(1)] = rec
    return out


BANKS = {"1010", "1020", "1030", "1050", "1060", "1080", "1120", "1140", "1150", "1180"}
ENERGY = {"2222", "2030", "2380", "2381", "2382", "4030"}
UTIL = {"5110", "2082", "2083", "2080", "2081"}
HEALTH = {"4002", "4004", "4005", "4007", "4009", "4013", "4014", "4017", "4018", "4019", "2070", "2230"}
STAPLES = {"4001", "4006", "4061", "4160", "4161", "4162", "4163", "4164"}
RETAIL = {"4003", "4008", "4011", "4012", "4050", "4051", "4190", "4191", "4192", "4193", "4194", "4240"}
TRANSPORT = {"4031", "4040", "4110", "4260", "4261", "4262", "4263", "2190"}
FOOD = {"2050", "2270", "2280", "2281", "2282", "2283", "2284", "2285", "2286", "2287", "2288",
        "6001", "6002", "6004", "6010", "6020", "6040", "6050", "6060", "6070", "6090"}
FINANCIAL = {"1182", "1183", "1111", "4080", "4081", "4082", "4083", "4084"}


def guess_sector(ticker, name):
    """Best guess for a new company; the monthly Claude check corrects anything wrong."""
    t = ticker
    if "reit" in name.lower() or "ريت" in name:
        return "REITs"
    if t.startswith("9"):
        return "Nomu"
    for group, label in ((BANKS, "Banks"), (ENERGY, "Energy"), (UTIL, "Utilities"), (HEALTH, "Health Care"),
                         (STAPLES, "Consumer Staples"), (RETAIL, "Retail"), (TRANSPORT, "Transportation"),
                         (FOOD, "Food & Beverages"), (FINANCIAL, "Financial Services")):
        if t in group:
            return label
    if t.startswith("70"):
        return "Telecom"
    if t.startswith("72"):
        return "Software & Services"
    if t.startswith("8"):
        return "Insurance"
    if "4300" <= t <= "4329":
        return "Real Estate"
    if t.startswith("18"):
        return "Consumer Services"
    if t.startswith(("2", "3", "12", "13")):
        return "Materials"
    return "Other"


def main():
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date()
    data = json.loads(DATA.read_text(encoding="utf-8"))

    cal = parse_calendar(flat(fetch("https://easysahm.com/calendar")))
    try:
        names_ar = parse_calendar_ar(flat(fetch("https://easysahm.com/ar/" + urllib.parse.quote("التقويم"))))
    except Exception as e:
        print(f"Arabic names skipped: {e}", file=sys.stderr)
        names_ar = {}
    payers = {}
    for page in range(1, 31):
        text = flat(fetch(f"https://easysahm.com/dividends?page={page}"))
        found = parse_payers(text)
        payers.update(found)
        m = re.search(r"Page (\d+) of (\d+)", text)
        if not found or not m or int(m.group(1)) >= int(m.group(2)):
            break
        time.sleep(1)
    if len(payers) < 50:
        raise RuntimeError(f"dividend payers page layout changed: only {len(payers)} companies parsed")
    print(f"calendar rows: {len(cal)}, Arabic names: {len(names_ar)}, dividend payers: {len(payers)}")

    events = data.get("events", [])
    index = {(e["ticker"], e.get("recordDate") or e.get("exDate")): e for e in events}
    added, changed = [], []

    def upsert(ticker, record_date, dps, pay_date, name):
        e = index.get((ticker, record_date))
        if e is None:
            # the same ticker within 3 days is the same dividend with a corrected date
            for (t, d), cand in index.items():
                if t == ticker and d and abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(record_date)).days) <= 3:
                    e = cand
                    break
        if e is None:
            e = {"ticker": ticker, "name": name, "sector": guess_sector(ticker, name), "dps": dps, "recordDate": record_date}
            if names_ar.get(ticker):
                e["nameAr"] = names_ar[ticker]
            if pay_date:
                e["payDate"] = pay_date
            events.append(e)
            index[(ticker, record_date)] = e
            added.append(f"{ticker} {name} {record_date}")
            return
        before = json.dumps(e, sort_keys=True, ensure_ascii=False)
        if pay_date and e.get("payDate") != pay_date:
            e["payDate"] = pay_date
        if dps and not e.get("dps"):
            e["dps"] = dps
        if json.dumps(e, sort_keys=True, ensure_ascii=False) != before:
            changed.append(f"{ticker} {record_date}")

    for r in cal:
        upsert(r["ticker"], r["recordDate"], r["dps"], r["payDate"], r["name"])
    for t, p in payers.items():
        if "next" in p and p["next"]["recordDate"] >= today.isoformat():
            upsert(t, p["next"]["recordDate"], p["next"]["dps"], None, p["name"])

    # refresh prices and trailing dividends for every event we hold
    for e in events:
        p = payers.get(e["ticker"])
        if p and "price" in p:
            e["price"], e["annualDps"] = p["price"], p["annualDps"]

    cutoff = (today - dt.timedelta(days=KEEP_DAYS)).isoformat()
    kept = [e for e in events if (e.get("payDate") or e.get("recordDate") or e.get("exDate") or "9999") >= cutoff]
    removed = [f"{e['ticker']} {e.get('recordDate')}" for e in events if e not in kept]
    kept.sort(key=lambda e: (e.get("recordDate") or e.get("exDate"), e["ticker"]))

    data["events"] = kept
    data["updated"] = today.isoformat()
    data["sample"] = False
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("added:", added or "none")
    print("changed:", changed or "none")
    print("removed:", removed or "none")


if __name__ == "__main__":
    main()
