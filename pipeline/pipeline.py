import json, argparse, pandas as pd
from collections import Counter
from pathlib import Path

from .model import Model
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
                rel = float(row.get("reliability") or "0.8")
            except Exception:
                rel = 0.8
            bias[d] = (bias_bin, rel)
    return bias


def cluster_summary(cluster, bias_map):
    # representative = most common title
    titles = [c.get("title", "Untitled") for c in cluster]
    rep_title = Counter(titles).most_common(1)[0][0]
    rep = next((c for c in cluster if c.get("title") == rep_title), cluster[0])

    sign = sum([c.get("sign", 0) for c in cluster]) / len(cluster)
    magnitude = sum([c.get("magnitude", 0) for c in cluster]) / len(cluster)
    reliability = sum(
        [bias_map.get(c.get("source", ""), ("center", 0.8))[1] for c in cluster]
    ) / len(cluster)
    bias_concentration = max(
        Counter(
            [bias_map.get(c.get("source", ""), ("center", 0.8))[0] for c in cluster]
        ).values()
    ) / len(cluster)

    return {
        "date": rep.get("date", ""),
        "component": rep.get("component", ""),
        "sign": round(sign, 2),
        "magnitude": round(magnitude, 2),
        "reliability": round(reliability, 2),
        "bias_max_share": round(bias_concentration, 2),
        "title": rep.get("title", "Untitled"),
    }


def compute_index(clusters):
    # Weighted index = Σ(sign × magnitude × reliability) / N
    if not clusters:
        return 0
    values = [
        c.get("sign", 0) * c.get("magnitude", 0) * c.get("reliability", 0.8)
        for c in clusters
    ]
    return round(sum(values) / len(values), 2)


def main(args):
    bias_map = load_bias_map()

    # fetch articles
    arts = fetch_articles(args.days, args.maxrecords)
    print("DEBUG: fetched articles:", len(arts))

    # cluster them
    clusters = cluster_titles([a["title"] for a in arts])
    print("DEBUG: Clusters:", len(clusters))

    # categorize (optional)
    categorized = categorize(clusters)

    # build cluster summaries
    summaries = [cluster_summary(c, bias_map) for c in categorized]

    # compute Humanity Index
    index_value = compute_index(summaries)

    # prepare outputs
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(args.output_dir) / "clusters.json", "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

    with open(Path(args.output_dir) / "latest.json", "w", encoding="utf-8") as f:
        json.dump({"date": pd.Timestamp.today().strftime("%Y-%m-%d"), "value": index_value}, f)

    print("Wrote data")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--maxrecords", type=int, default=100)
    parser.add_argument("--output-dir", type=str, default="data")
    args = parser.parse_args()
    main(args)
