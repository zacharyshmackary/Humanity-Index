import time
import datetime as dt
from urllib.parse import urlencode
import requests

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

def _parse_date(seen: str) -> str:
    if not seen:
        return dt.date.today().isoformat()
    s = str(seen).strip().replace("Z", "").replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y%m%d %H%M%S", "%Y-%m-%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s[:len(fmt)], fmt).date().isoformat()
        except Exception:
            pass
    return dt.date.today().isoformat()

def _get_json_with_retries(url: str, retries: int = 4, backoff: float = 1.5):
    delay = 1.0
    last_err = None
    for _ in range(retries):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            time.sleep(delay)
            delay *= backoff
    raise last_err

def fetch_articles(days: int = 2, maxrecords: int = 150):
    params = {
        "query": "*",
        "mode": "ArtList",
        "maxrecords": maxrecords,   # keep modest to avoid 429s
        "format": "json",
        "timespan": f"{days}d",
        "sort": "datedesc",
    }
    url = f"{GDELT_DOC_API}?{urlencode(params)}"
    data = _get_json_with_retries(url)
    out = []
    for a in data.get("articles", []):
        title = (a.get("title") or "").strip()
        url = (a.get("url") or "").strip()
        domain = (a.get("domain") or "").strip().lower()
        seen = a.get("seendate") or a.get("date") or ""
        date = _parse_date(seen)
        if title and url and domain:
            out.append({"title": title, "url": url, "domain": domain, "date": date})
    return out
