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
    # representative title (most common string)
    rep = max(cluster, key=lambda x: Counter([c["title"] for c in cluster])[x["title"]])
    sign = sum([c["sign"] for c in cluster]) / len(cluster)
    magnitude = sum([c["magnitude"] for c in cluster]) / len(cluster)
    reliability = sum([bias_map.get(c["source"], ("center", 0.8))[1] for c in cluster]) / len(cluster)
    bias_concentration = max(Counter([bias_map.get(c["source"], ("center", 0.8))[0] for c in cluster]).values()) / len(cluster)
    return {
        "date": rep["date"],
        "component": rep["component"],
        "sign": round(sign, 2),
        "magnitude": round(magnitude, 2),
        "reliability": round(reliability, 2),
        "bias_max_share": round(bias_concentration, 2),
        "title": rep["title"]
    }


def main(days=1, maxrecords=100, output_dir="data"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # fetch
    articles = fetch_articles(days=days, maxrecords=maxrecords)
    print("DEBUG: fetched articles:", len(articles))

    # cluster
    clusters = cluster_titles(articles)
    print("DEBUG: clusters:", len(clusters))

    # bias map
    bias_map = load_bias_map()

    # summarize clusters
    summaries = [cluster_summary(c, bias_map) for c in clusters]
    with open(Path(output_dir) / "clusters.json", "w") as f:
        json.dump(summaries, f, indent=2)

    # compute Humanity Index
    hi_model = HIModel()
    hi_value = hi_model.compute(summaries)

    latest = {
        "date": str(pd.Timestamp.today().date()),
        "value": hi_value  # 🔥 FIX: was "hi"
    }
    with open(Path(output_dir) / "latest.json", "w") as f:
        json.dump(latest, f, indent=2)

    # append to time series
    index_series_path = Path(output_dir) / "index_series.json"
    if index_series_path.exists():
        with open(index_series_path) as f:
            series = json.load(f)
    else:
        series = []
    series.append(latest)
    with open(index_series_path, "w") as f:
        json.dump(series, f, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--maxrecords", type=int, default=100)
    parser.add_argument("--output-dir", type=str, default="data")
    args = parser.parse_args()

    main(days=args.days, maxrecords=args.maxrecords, output_dir=args.output_dir)
