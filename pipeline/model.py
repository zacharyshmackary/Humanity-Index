import pandas as pd, numpy as np, yaml

class HIModel:
    def __init__(self, settings="settings.yaml"):
        cfg = yaml.safe_load(open(settings))
        self.alpha = float(cfg["alpha"])
        self.bias_threshold = float(cfg["bias_threshold"])
        self.bias_penalty = float(cfg["bias_penalty"])
        # keep weights as a dict
        self.weights = dict(cfg["components"])

    def compute(self, df):
        df = df.copy()

        # bias penalty
        df["b"] = np.where(df["bias_max_share"] >= self.bias_threshold, self.bias_penalty, 1.0)

        # per-cluster contribution
        df["delta"] = df["sign"] * df["magnitude"] * df["reliability"] * df["b"]

        # daily component totals (some components may be missing on a given day)
        comp = df.groupby(["date", "component"])["delta"].sum().unstack(fill_value=0.0)

        # z-score per component vs mean/std of the period we have
        mu = comp.mean()
        sigma = comp.std().replace(0, 1e-6)  # guard against divide-by-zero
        z = (comp - mu) / sigma

        # ALIGN WEIGHTS to the columns we actually have (A/B/C/D/E subset)
        w = pd.Series(self.weights)
        w = w.reindex(z.columns, fill_value=0.0)

        # composite Z and HI
        Z = (z * w).sum(axis=1)
        HI = (100 * np.tanh(self.alpha * Z)).astype(int)

        # make a simple list of {date, HI}
        out = []
        for d, h in HI.items():
            # d is already a string index if your input 'date' was strings;
            # if it's Timestamp, convert to YYYY-MM-DD:
            if hasattr(d, "strftime"):
                ds = d.strftime("%Y-%m-%d")
            else:
                ds = str(d)
            out.append({"date": ds, "HI": int(h)})
        return out
