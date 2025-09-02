import json, argparse, pandas as pd
from .model import HIModel

def run(output_dir="data"):
    # Dummy input — replace with real fetch later
    df = pd.DataFrame([
        {"date":"2025-08-30","component":"A","sign":-1,"magnitude":0.5,"reliability":0.9,"bias_max_share":0.6},
        {"date":"2025-08-30","component":"B","sign":1,"magnitude":0.7,"reliability":0.9,"bias_max_share":0.6},
    ])
    hi = HIModel().compute(df)
    with open(f"{output_dir}/latest.json","w") as f: json.dump(hi[-1],f,indent=2)
    with open(f"{output_dir}/index_series.json","w") as f: json.dump(hi,f,indent=2)
    print("Wrote data")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="data")
    args=ap.parse_args()
    run(args.output_dir)
