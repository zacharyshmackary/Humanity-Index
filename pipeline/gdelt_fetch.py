import requests, datetime as dt
from urllib.parse import urlencode

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

def fetch_articles(days=1, maxrecords=250):
    """
    Returns a list of dicts with keys: title, url, domain, seendate (YYYY-MM-DD)
    """
    params = {
        "query": "*",               # all news
        "mode": "ArtList",          # article list
        "maxrecords": maxrecords,   # cap per request
        "format": "json",
        "timespan": f"{days}d",     # e.g. '1d', '2d'
        "sort": "datedesc"
    }
    url = f"{GDELT_DOC_API}?{urlencode(params)}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    arts = []
    for a in data.get("articles", []):
        title = (a.get("title") or "").strip()
        url = (a.get("url") or "").strip()
        domain = (a.get("domain") or "").strip().lower()
        # seendate can be '2025-09-01T12:34:56Z' or '20250901T123456Z' depending on feed
        seen = a.get("seendate") or a.get("date")
        date = None
        if seen:
            s = str(seen).replace("Z","").replace("T"," ")
            try:
                date = dt.datetime.fromisoformat(s).date().isoformat()
            except Exception:
                try:
                    date = dt.datetime.strptime(str(seen), "%Y%m%dT%H%M%S").date().isoformat()
                except Exception:
                    date = dt.date.today().isoformat()
        else:
            date = dt.date.today().isoformat()
        if title and url and domain:
            arts.append({"title": title, "url": url, "domain": domain, "date": date})
    return arts
