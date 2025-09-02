import json, argparse, pandas as pd
from collections import Counter, defaultdict
from .model import HIModel
from .gdelt_fetch import fetch_articles
from .cluster import cluster_titles
from pathlib import Path

def load_bias_map(path="data/bias_ratings.csv"):
    import csv
    bias = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = (row.get("domain") or "").strip().lower()
            if not d: continue
            bias_bin = (row.get("bias_bin") or "center").strip().lower()
            try:
                rel = float(row.get("reliability", "0.8"))
            except Exception:
                rel = 0.8
            bias[d] = (bias_bin, rel)
    return bias

def categorize_cluster(cluster):
    from .categorize import categorize
    # choose representative title = longest
    rep = max(cluster, key=lambda x: len(x["title"]))
    comp, sign, mag = categorize(rep["title"])
    return comp, sign, mag, rep["title"]

def clusters_to_rows(clusters, bias_map):
    rows = []
    for cl in clusters:
        # majority date in cluster
        date = Counter([it["date"] for it in cl]).most_common(1)[0][0]
        # reliability = average of domains; bias share = max share by bias_bin
        rels, bias_bins = [], []
        for it in cl:
            bias_bin, rel = bias_map.get(it["domain"], ("center", 0.8))
            rels.append(rel)
            bias_bins.append(bias_bin)
        reliability = sum(rels)/max(1,len(rels))
        share = Counter(bias_bins)
        total = sum(share.values())
        bias_max_share = max(share.values())/total if total else 0.0

        comp, sign, mag, _ = categorize_cluster(cl)
        rows.append({
            "date": date,
            "component": comp,
            "sign": sign,
            "magnitude": mag,
            "reliability": reliability,
            "bias_max_share": bias_max_share
        })
    return pd.DataFrame(rows)

def run(output_dir="data", days=1, maxrecords=250):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        arts = fetch_articles(days=days, maxrecords=maxrecords)
    except Exception as e:
        print("Fetch failed:", e)
        arts = []

    if not arts:
        # Very minimal fallback so the site doesn't go blank
        import datetime as dt
        d = dt.date.today().isoformat()
        df = pd.DataFrame([
            {"date": d, "component":"D", "sign": 1, "magnitude":0.4, "reliability":0.85, "bias_max_share":0.6}
        ])
    else:
        # Cluster near-duplicate headlines
        clusters = cluster_titles(arts, threshold=0.28, max_clusters=150)
        bias_map = load_bias_map()
        df = clusters_to_rows(clusters, bias_map)

    hi = HIModel().compute(df)  # list of {"date":"YYYY-MM-DD","HI":int}
    latest_obj = hi[-1]
    out_latest = {"date": latest_obj["date"], "hi": latest_obj["HI"]}

    with open(f"{output_dir}/latest.json", "w") as f:
        json.dump(out_latest, f, indent=2)
    with open(f"{output_dir}/index_series.json", "w") as f:
        json.dump(hi, f, indent=2)

    print("Wrote data")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="data")
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--maxrecords", type=int, default=250)
    ap.add_argument("--append-history", action="store_true", help="(optional) not used in minimal starter")
    args = ap.parse_args()
    run(args.output_dir, args.days, args.maxrecords)
