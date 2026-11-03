#!/usr/bin/env python3
"""Build data/us.json: AAOIFI screening inputs for US stocks.

Financials come from SEC EDGAR's XBRL "company facts" API (official, free).
Industry comes from the company's SIC code in EDGAR.
Prices come from Stooq's free daily quotes, with Yahoo Finance as a fallback.

Standard library only, so the GitHub Action needs no installs.
"""
import json, os, sys, time, urllib.request, urllib.error, csv, io
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "labs", "shariah-compliant", "data")
UA = os.environ.get("SEC_USER_AGENT") or "HalalScreen rafkhan.com/labs/shariah-compliant admin@rafkhan.com"
SEC_DELAY = 0.15  # SEC asks for at most 10 requests a second


def get(url, ua=UA, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:
                raise
            time.sleep(2 * (i + 1))
        except Exception as e:  # network blip
            last = e
            time.sleep(2 * (i + 1))
    raise last


def sec_json(url):
    time.sleep(SEC_DELAY)
    return json.loads(get(url))


# ---------- XBRL helpers ----------
FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "10-KT"}


def entries(facts, tag, unit="USD", ns="us-gaap"):
    t = facts.get(ns, {}).get(tag)
    if not t:
        return []
    return [e for e in t.get("units", {}).get(unit, []) if e.get("form") in FORMS]


def days(a, b):
    return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)


def instant(facts, tag, on, unit="USD", ns="us-gaap"):
    """Value of an instant fact at balance-sheet date `on` (latest filing wins)."""
    es = [e for e in entries(facts, tag, unit, ns) if e["end"] == on and "start" not in e]
    if not es:
        return None
    return sorted(es, key=lambda e: e["filed"])[-1]["val"]


def latest_instant(facts, tag, unit="USD", ns="us-gaap"):
    es = [e for e in entries(facts, tag, unit, ns) if "start" not in e]
    if not es:
        return None
    e = sorted(es, key=lambda e: (e["end"], e["filed"]))[-1]
    return e


def annual(facts, tag, unit="USD"):
    """Latest full fiscal-year value (duration 350-380 days) from a 10-K."""
    es = [e for e in entries(facts, tag, unit) if "start" in e and e["form"].startswith("10-K")
          and 350 <= days(e["start"], e["end"]) <= 380]
    if not es:
        return None
    return sorted(es, key=lambda e: (e["end"], e["filed"]))[-1]


def annual_at(facts, tag, end):
    es = [e for e in entries(facts, tag) if "start" in e and e["end"] == end
          and 350 <= days(e["start"], e["end"]) <= 380]
    if not es:
        return None
    return sorted(es, key=lambda e: e["filed"])[-1]["val"]


# ---------- the four inputs ----------
def balance_date(facts):
    for tag in ("Assets", "LiabilitiesAndStockholdersEquity"):
        e = latest_instant(facts, tag)
        if e:
            return e["end"], e
    return None, None


def debt(facts, on):
    """Interest-bearing debt at `on`. Tries combined tags first so nothing is counted twice."""
    v = lambda t: instant(facts, t, on)
    parts = []
    # long-term debt including its current portion
    if v("LongTermDebt") is not None:
        parts.append(("LongTermDebt", v("LongTermDebt")))
    elif v("LongTermDebtNoncurrent") is not None or v("LongTermDebtCurrent") is not None:
        for t in ("LongTermDebtNoncurrent", "LongTermDebtCurrent"):
            if v(t) is not None:
                parts.append((t, v(t)))
    elif v("LongTermDebtAndCapitalLeaseObligations") is not None:
        for t in ("LongTermDebtAndCapitalLeaseObligations", "LongTermDebtAndCapitalLeaseObligationsCurrent"):
            if v(t) is not None:
                parts.append((t, v(t)))
    elif v("DebtLongtermAndShorttermCombinedAmount") is not None:
        return [("DebtLongtermAndShorttermCombinedAmount", v("DebtLongtermAndShorttermCombinedAmount"))]
    elif v("LongTermDebtNoncurrent") is None and v("DebtCurrent") is not None:
        pass
    # short-term borrowings (commercial paper is usually inside ShortTermBorrowings)
    if v("ShortTermBorrowings") is not None:
        parts.append(("ShortTermBorrowings", v("ShortTermBorrowings")))
    elif v("CommercialPaper") is not None:
        parts.append(("CommercialPaper", v("CommercialPaper")))
    elif not parts and v("DebtCurrent") is not None:
        parts.append(("DebtCurrent", v("DebtCurrent")))
    return parts


def cash(facts, on):
    """Cash and short-term interest-bearing investments at `on` (conservative: all cash counts)."""
    v = lambda t: instant(facts, t, on)
    parts = []
    for t in ("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash"):
        if v(t) is not None:
            parts.append((t, v(t)))
            break
    for t in ("ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
              "HeldToMaturitySecuritiesCurrent"):
        if v(t) is not None:
            parts.append((t, v(t)))
            break
    return parts


REVENUE_TAGS = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
                "RevenuesNetOfInterestExpense", "InterestAndDividendIncomeOperating")


def revenue(facts):
    best = None
    for t in REVENUE_TAGS:
        e = annual(facts, t)
        if e and (best is None or e["end"] > best[1]["end"] or (e["end"] == best[1]["end"] and e["val"] > best[1]["val"])):
            best = (t, e)
    return best


INTEREST_TAGS = ("InvestmentIncomeInterest", "InterestIncomeOther", "InvestmentIncomeInterestAndDividend",
                 "InterestAndDividendIncomeOperating", "InterestIncomeOperating", "InterestAndOtherIncome")


def interest_income(facts, fy_end):
    for t in INTEREST_TAGS:
        val = annual_at(facts, t, fy_end)
        if val is not None:
            return t, max(val, 0), "reported"
    val = annual_at(facts, "InterestIncomeExpenseNonoperatingNet", fy_end)
    if val is not None and val > 0:
        return "InterestIncomeExpenseNonoperatingNet", val, "net"
    return None, None, "missing"


def shares(facts):
    best = None
    for ns, t, unit in (("dei", "EntityCommonStockSharesOutstanding", "shares"),
                        ("us-gaap", "CommonStockSharesOutstanding", "shares"),
                        ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding", "shares")):
        es = [e for e in facts.get(ns, {}).get(t, {}).get("units", {}).get(unit, [])]
        if not es:
            continue
        last_end = max(e["end"] for e in es)
        # several share classes can share one date: add them up
        same = {}
        for e in es:
            if e["end"] == last_end:
                same[e.get("frame") or e["accn"] + str(e["val"])] = e["val"]
        latest = sorted([e for e in es if e["end"] == last_end], key=lambda e: e["filed"])[-1]
        tot = sum(e["val"] for e in es if e["end"] == last_end and e["accn"] == latest["accn"])
        cand = (t, tot, last_end)
        if best is None or last_end > best[2]:
            best = cand
        if t == "EntityCommonStockSharesOutstanding":
            return cand
    return best


# ---------- business activity from SIC ----------
def business(sic, name):
    s = int(sic) if sic and str(sic).isdigit() else 0
    n = (name or "").lower()
    if 6000 <= s <= 6499:
        return "finance"
    if s in (2082, 2084, 2085, 5813, 5921):
        return "alcohol"
    if 2100 <= s <= 2199:
        return "tobacco"
    if s == 7993:
        return "gambling"
    if 3480 <= s <= 3489 or 3760 <= s <= 3769 or s in (3812, 3795):
        return "defense"
    if 6700 <= s <= 6799 or s in (2011, 2013, 5812, 7011, 7990) or 7800 <= s <= 7899 or s in (4833, 4841):
        return "review"
    return "ok"


OVERRIDES_PATH = os.path.join(DATA, "overrides-us.json")


# ---------- prices ----------
def price(ticker):
    sym = ticker.replace(".", "-")
    try:
        raw = get(f"https://stooq.com/q/l/?s={sym.lower()}.us&f=sd2c&h&e=csv", ua="Mozilla/5.0").decode()
        row = next(csv.DictReader(io.StringIO(raw)))
        p = float(row["Close"])
        if p > 0:
            return p, row["Date"], "Stooq"
    except Exception:
        pass
    try:
        j = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d", ua="Mozilla/5.0"))
        m = j["chart"]["result"][0]["meta"]
        return float(m["regularMarketPrice"]), datetime.fromtimestamp(m["regularMarketTime"], timezone.utc).date().isoformat(), "Yahoo Finance"
    except Exception:
        return None, None, None


def main():
    tickers = [l.strip().upper() for l in open(os.path.join(DATA, "universe-us.txt"))
               if l.strip() and not l.startswith("#")]
    only = sys.argv[1:]
    if only:
        tickers = [t for t in tickers if t in only] or only
    overrides = json.load(open(OVERRIDES_PATH)) if os.path.exists(OVERRIDES_PATH) else {}

    cikmap = {v["ticker"].upper(): (str(v["cik_str"]).zfill(10), v["title"])
              for v in json.loads(get("https://www.sec.gov/files/company_tickers.json")).values()}

    out, skipped = {}, {}
    for t in tickers:
        key = t.replace(".", "-")
        if key not in cikmap and t not in cikmap:
            skipped[t] = "Ticker not found in SEC EDGAR"
            continue
        cik, title = cikmap.get(key) or cikmap.get(t)
        try:
            sub = sec_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
            facts = sec_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json").get("facts", {})
        except Exception as e:
            skipped[t] = f"EDGAR request failed: {e}"
            continue
        if "us-gaap" not in facts:
            skipped[t] = "Files IFRS reports (foreign company), not supported yet"
            continue
        on, _ = balance_date(facts)
        rev = revenue(facts)
        if not on or not rev:
            skipped[t] = "Balance sheet or revenue missing in EDGAR data"
            continue
        d, c = debt(facts, on), cash(facts, on)
        itag, ival, iquality = interest_income(facts, rev[1]["end"])
        sh = shares(facts)
        p, pdate, psrc = price(t)
        if not p or not sh:
            skipped[t] = "No price or share count"
            continue
        biz = business(sub.get("sic"), sub.get("name"))
        ov = overrides.get(t, {})
        biz = ov.get("biz", biz)
        mcap = p * sh[1]
        rec = {
            "name": sub.get("name") or title,
            "cik": cik,
            "exchange": (sub.get("exchanges") or [None])[0],
            "sic": sub.get("sic"), "sicDesc": sub.get("sicDescription"),
            "biz": biz, "bizNote": ov.get("note"),
            "price": round(p, 4), "priceDate": pdate, "priceSource": psrc,
            "shares": sh[1], "sharesDate": sh[2],
            "marketCap": round(mcap),
            "balanceDate": on,
            "debt": sum(v for _, v in d), "debtParts": d,
            "cash": sum(v for _, v in c), "cashParts": c,
            "revenue": rev[1]["val"], "revenueTag": rev[0], "fiscalYearEnd": rev[1]["end"],
            "nonPermissible": ival, "nonPermissibleTag": itag, "nonPermissibleQuality": iquality,
            "filing": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K",
        }
        out[t] = rec
        print(f"{t:6} {biz:8} mcap {mcap/1e9:8.1f}B debt {rec['debt']/mcap:6.1%} cash {rec['cash']/mcap:6.1%} "
              f"income {(ival or 0)/rev[1]['val']:6.1%} ({iquality})", flush=True)

    path = os.path.join(DATA, "us.json")
    json.dump({"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "sources": {"financials": "SEC EDGAR XBRL company facts", "prices": "Stooq / Yahoo Finance daily close"},
               "stocks": out, "skipped": skipped},
              open(path, "w"), separators=(",", ":"))
    print(f"\n{len(out)} screened, {len(skipped)} skipped")
    for k, v in skipped.items():
        print(f"  skipped {k}: {v}")
    if len(out) == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
