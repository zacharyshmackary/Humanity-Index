import json, argparse, pandas as pd
from collections import Counter
from pathlib import Path

from .model import HIModel
from .gdelt_fetch import fetch_articles
from .cluster import cluster_titles
from .categorize import categorize


def load_bias_map(path="data/bias_ratings.csv"):
    import csv
    bias = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = (row.get("domain") or "").strip().lower()
            if not d:
                continue
            bias_bin = (row.get("bias_bin") or "center").strip().lower()
            try:
                rel = float(row.get("reliability", "0.8"))
            except Exception:
                rel = 0.8
            bias[d] = (bias_bin, rel)
    return bias


def cluster_summary(cluster, bias_map):
    # representative title (longest title)
    rep = max(cluster, key=lambda x: len(x["title"]))
    comp, sign, mag = categorize(rep["title"])

    # majority date
    date = Counter([it["date"] for it in cluster]).most_common(1)[0][0]

    # reliability & bias share
    rels, bins = [], []
    for it in cluster:
        bias_bin, rel = bias_map.get(it["domain"], ("center", 0.8))
        rels.append(rel)
        bins.append(bias_bin)
    reliability = sum(rels) / max(1, len(rels))
    counts = Counter(bins)
    total = sum(counts.values())
    bias_max_share = max(counts.values()) / total if total else 0.0

    return {
        "date": date,
        "component": comp,
        "sign": sign,
        "magnitude": mag,
        "reliability": reliability,
        "bias_max_share": bias_max_share,
        "title": rep["title"],
    }


def run(output_dir="data", days=2, maxrecords=150):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    bias_map = load_bias_map()
    try:
        arts = fetch_articles(days=days, maxrecords=maxrecords)
    except Exception as e:
        print("Fetch failed:", e)
        arts = []

    # If no articles, keep site alive with a tiny fallback
    if not arts:
        import datetime as dt
        d = dt.date.today().isoformat()
        clusters = [[{"title": "fallback civics story", "domain": "apnews.com", "date": d}]]
    else:
        clusters = cluster_titles(
            arts,
            threshold=0.28,
            max_clusters=150
        )

    summaries = [cluster_summary(c, bias_map) for c in clusters]

    # DF for the model
    df = pd.DataFrame([
        {k: v for k, v in s.items()
         if k in ("date", "component", "sign", "magnitude", "reliability", "bias_max_share")}
        for s in summaries
    ])

    hi = HIModel().compute(df)  # [{"date":"YYYY-MM-DD","HI":int}]
    latest_obj = hi[-1]
    out_latest = {"date": latest_obj["date"], "hi": latest_obj["HI"]}

    with open(f"{output_dir}/latest.json", "w") as f:
        json.dump(out_latest, f, indent=2)
    with open(f"{output_dir}/index_series.json", "w") as f:
        json.dump(hi, f, indent=2)
    with open(f"{output_dir}/clusters.json", "w") as f:
        json.dump(summaries, f, indent=2)

    print("Wrote data")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="data")
    ap.add_argument("--days", type=int, default=2)
    ap.add_argument("--maxrecords", type=int, default=150)
    args = ap.parse_args()
    run(args.output_dir, args.days, args.maxrecords)
