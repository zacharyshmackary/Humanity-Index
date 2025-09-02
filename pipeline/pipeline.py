# pipeline/pipeline.py
import json
import argparse
import pandas as pd
from collections import defaultdict
from pathlib import Path

# ✅ FIXED import
from pipeline.model import Model as HModel
from pipeline.gdelt_fetch import fetch_articles
from pipeline.categorize import categorize
from pipeline.cluster import cluster_titles


def build_clusters(articles):
    """
    Make one representative cluster per component (A..E).
    Each cluster dict contains: date, component, sign, magnitude,
    reliability, bias_max_share, title.
    """
    buckets = defaultdict(list)
    for a in articles:
        comp = a.get("component") or categorize(a.get("title", ""))
        a = dict(a)  # copy
        a["component"] = comp
        # ensure required keys exist
        a.setdefault("sign", 1)
        a.setdefault("magnitude", 0.6)
        a.setdefault("reliability", 0.9)
        a.setdefault("bias_max_share", 1.0)
        a.setdefault("date", a.get("date"))
        buckets[comp].append(a)

    clusters = []
    for comp, items in buckets.items():
        if not items:
            continue
        # aggregate sign by majority
        s = 1 if sum(x.get("sign", 1) for x in items) >= 0 else -1
        # simple aggregates
        mag = sum(x.get("magnitude", 0.6) for x in items) / len(items)
        rel = sum(float(x.get("reliability", 0.9)) for x in items) / len(items)
        bias = max(float(x.get("bias_max_share", 1.0)) for x in items)
        date = items[0].get("date", "")
        titles = cluster_titles([it.get("title", "") for it in items])
        title = titles[0] if titles else ""
        clusters.append({
            "date": date,
            "component": comp,
            "sign": int(s),
            "magnitude": float(mag),
            "reliability": float(rel),
            "bias_max_share": float(bias),
            "title": title,
        })
    # keep at most A..E in stable order
    order = ["A", "B", "C", "D", "E"]
    clusters.sort(key=lambda c: order.index(c["component"]) if c["component"] in order else 99)
    return clusters


def run(output_dir="public/data", days=1, maxrecords=30):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 1) Fetch articles (real or fallback inside fetch_articles)
    articles = fetch_articles(days=days, maxrecords=maxrecords)

    # 2) Build clusters for transparency
    clusters = build_clusters(articles)

    # 3) Build DataFrame for the model
    rows = []
    for c in clusters:
        rows.append({
            "date": c["date"],
            "component": c["component"],
            "sign": c["sign"],
            "magnitude": c["magnitude"],
            "reliability": c["reliability"],
            "bias_max_share": c["bias_max_share"],
        })
    df = pd.DataFrame(rows)

    # 4) Compute HI time series
    hi_series = HModel().compute(df)  # list of {"date": "...", "HI": int}

    # 5) Write files the site expects
    latest_obj = hi_series[-1] if hi_series else {"date": None, "HI": 0}
    latest = {"date": latest_obj["date"], "hi": int(latest_obj["HI"])}

    with open(f"{output_dir}/latest.json", "w") as f:
        json.dump(latest, f, indent=2)

    with open(f"{output_dir}/index_series.json", "w") as f:
        json.dump(hi_series, f, indent=2)

    with open(f"{output_dir}/clusters.json", "w") as f:
        json.dump(clusters, f, indent=2)

    print("wrote data")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="public/data")
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--maxrecords", type=int, default=30)
    args = ap.parse_args()
    run(output_dir=args.output_dir, days=args.days, maxrecords=args.maxrecords)
