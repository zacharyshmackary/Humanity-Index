import json, argparse, pandas as pd
from .model import HIModel


def run(output_dir="data"):
    # Dummy input — replace with real fetch later
    df = pd.DataFrame([
        {"date":"2025-08-25","component":"A","sign":-1,"magnitude":0.5,"reliability":0.9,"bias_max_share":0.6},
        {"date":"2025-08-25","component":"B","sign": 1,"magnitude":0.7,"reliability":0.9,"bias_max_share":0.6},
        {"date":"2025-08-26","component":"A","sign": 1,"magnitude":0.8,"reliability":0.9,"bias_max_share":0.6},
        {"date":"2025-08-27","component":"B","sign":-1,"magnitude":0.6,"reliability":0.9,"bias_max_share":0.6},
        {"date":"2025-08-28","component":"C","sign": 1,"magnitude":0.9,"reliability":0.8,"bias_max_share":0.5},
        {"date":"2025-08-29","component":"D","sign":-1,"magnitude":0.7,"reliability":0.85,"bias_max_share":0.7},
        {"date":"2025-08-30","component":"E","sign": 1,"magnitude":1.0,"reliability":0.95,"bias_max_share":0.4},
    ])

    hi = HIModel().compute(df)

    # Write latest.json with lowercase "hi" key (what the web page expects)
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
