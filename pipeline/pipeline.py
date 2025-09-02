import json, argparse, pandas as pd
from datetime import datetime, timedelta
from .model import HIModel

def run(output_dir="data"):
    # Rolling 7 days relative to today (UTC)
    today = datetime.utcnow().date()
    days = [(today - timedelta(days=d)).strftime("%Y-%m-%d") for d in range(6, -1, -1)]

    rows = []
    rows += [
        {"date": days[0], "component":"A","sign":-1,"magnitude":0.5,"reliability":0.9,"bias_max_share":0.6},
        {"date": days[0], "component":"B","sign": 1,"magnitude":0.7,"reliability":0.9,"bias_max_share":0.6},
    ]
    rows += [
        {"date": days[1], "component":"A","sign": 1,"magnitude":0.8,"reliability":0.9,"bias_max_share":0.6},
        {"date": days[1], "component":"B","sign":-1,"magnitude":0.6,"reliability":0.9,"bias_max_share":0.6},
    ]
    rows += [
        {"date": days[2], "component":"C","sign": 1,"magnitude":0.9,"reliability":0.8,"bias_max_share":0.5},
        {"date": days[3], "component":"D","sign":-1,"magnitude":0.7,"reliability":0.85,"bias_max_share":0.7},
        {"date": days[4], "component":"E","sign": 1,"magnitude":1.0,"reliability":0.95,"bias_max_share":0.4},
        {"date": days[5], "component":"B","sign": 1,"magnitude":0.6,"reliability":0.9,"bias_max_share":0.6},
        {"date": days[6], "component":"A","sign":-1,"magnitude":0.6,"reliability":0.9,"bias_max_share":0.6},
    ]
    df = pd.DataFrame(rows)

    hi = HIModel().compute(df)
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
    args = ap.parse_args()
    run(args.output_dir)
