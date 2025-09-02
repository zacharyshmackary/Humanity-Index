import requests, datetime as dt
from urllib.parse import urlencode

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

def fetch_articles(days=1, maxrecords=250):
    params = {
        "query": "*",
        "mode": "ArtList",
        "maxrecords": maxrecords,
        "format": "json",
        "timespan": f"{days}d",   # 1d = 24h, bump to 2d or 3d if empty
        "sort": "datedesc"
    }
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
        date = None
        if seen:
            s = str(seen).replace("Z","").replace("T"," ")
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y%m%d %H%M%S", "%Y-%m-%d"):
                try:
                    date = dt.datetime.strptime(s[:len(fmt)], fmt).date().isoformat()
                    break
                except Exception:
                    pass
        if not date:
            date = dt.date.today().isoformat()
        if title and url and domain:
            out.append({"title": title, "url": url, "domain": domain, "date": date})
    return out
