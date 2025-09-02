import time
import datetime as dt
from urllib.parse import urlencode
import requests

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"


def _parse_date(seen: str) -> str:
    """Convert seendate variants to YYYY-MM-DD (UTC)."""
    if not seen:
        return dt.date.today().isoformat()
    s = str(seen).strip().replace("Z", "").replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y%m%d %H%M%S", "%Y-%m-%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s[:len(fmt)], fmt).date().isoformat()
        except Exception:
            pass
    return dt.date.today().isoformat()


def _get_json_with_retries(url: str, retries: int = 4, backoff: float = 1.6):
    """GET with simple backoff; raise last error if all attempts fail."""
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


def _fallback_articles():
    """Small mixed sample so the pipeline still produces HI values."""
    today = dt.date.today().isoformat()
    return [
        {"title": "Border clashes escalate despite ceasefire talks",
         "url": "https://example.com/1", "domain": "reuters.com", "date": today},
        {"title": "Severe floods displace thousands after torrential rains",
         "url": "https://example.com/2", "domain": "bbc.co.uk", "date": today},
        {"title": "Court upholds anti-corruption reforms increasing transparency",
         "url": "https://example.com/3", "domain": "apnews.com", "date": today},
        {"title": "Cancer trial reports promising new therapy in early results",
         "url": "https://example.com/4", "domain": "nytimes.com", "date": today},
        {"title": "International donors pledge relief funds for affected regions",
         "url": "https://example.com/5", "domain": "guardian.com", "date": today},
    ]


def fetch_articles(days: int = 1, maxrecords: int = 30):
    """
    Return list of dicts: {title, url, domain, date}.
    Uses fallback if the API is empty or rate-limited.
    """
    params = {
        "query": "*",
        "mode": "ArtList",
        "maxrecords": maxrecords,
        "format": "json",
        "timespan": f"{days}d",
        "sort": "datedesc",
    }
    url = f"{GDELT_DOC_API}?{urlencode(params)}"
    try:
        data = _get_json_with_retries(url)
        out = []
        for a in data.get("articles", []):
            title = (a.get("title") or "").strip()
            link = (a.get("url") or "").strip()
            domain = (a.get("domain") or "").strip().lower()
            seen = a.get("seendate") or a.get("date") or ""
            date = _parse_date(seen)
            if title and link and domain:
                out.append({"title": title, "url": link, "domain": domain, "date": date})
        if not out:
            print("⚠️ GDELT returned no articles; using fallback.")
            return _fallback_articles()
        return out
    except Exception as e:
        print("⚠️ GDELT fetch failed; using fallback. Error:", e)
        return _fallback_articles()
        
