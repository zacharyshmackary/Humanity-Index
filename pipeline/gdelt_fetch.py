import datetime as dt
from urllib.parse import urlencode

import requests

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


def _parse_date(seen: str) -> str:
    """
    Convert a variety of seendate formats from GDELT into YYYY-MM-DD (UTC).
    Falls back to today's date if parsing fails.
    """
    if not seen:
        return dt.date.today().isoformat()

    s = str(seen).strip().replace("Z", "").replace("T", " ")
    # Try a few common formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y%m%d %H%M%S", "%Y-%m-%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s[:len(fmt)], fmt).date().isoformat()
        except Exception:
            continue
    return dt.date.today().isoformat()


def fetch_articles(days: int = 1, maxrecords: int = 250):
    """
    Fetch recent articles from GDELT Doc API.

    Returns a list of dicts with keys:
      - title (str)
      - url (str)
      - domain (str, lowercase)
      - date (YYYY-MM-DD)
    """
    params = {
        "query": "*",               # all news
        "mode": "ArtList",          # article list output
        "maxrecords": maxrecords,   # cap
        "format": "json",
        "timespan": f"{days}d",     # e.g. '1d', '2d', ...
        "sort": "datedesc",
    }
    url = f"{GDELT_DOC_API}?{urlencode(params)}"

    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()

    out = []
    for a in data.get("articles", []):
        title = (a.get("title") or "").strip()
        url = (a.get("url") or "").strip()
        domain = (a.get("domain") or "").strip().lower()
        seen = a.get("seendate") or a.get("date") or ""

        date = _parse_date(seen)

        if title and url and domain:
            out.append({
                "title": title,
                "url": url,
                "domain": domain,
                "date": date,
            })
    return out
