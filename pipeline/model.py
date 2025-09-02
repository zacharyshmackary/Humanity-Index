import pandas as pd, numpy as np, yaml


class HIModel:
    def __init__(self, settings="settings.yaml"):
        cfg = yaml.safe_load(open(settings))
        self.alpha = float(cfg["alpha"])
        self.bias_threshold = float(cfg["bias_threshold"])
        self.bias_lambda = float(cfg.get("bias_lambda", 0.6))
        self.weights = dict(cfg["components"])
        hist = cfg.get("history", {})
        self.min_days_for_stats = int(hist.get("min_days_for_stats", 14))
        self.rolling_days = int(hist.get("rolling_days", 0))

    def _bias_penalty(self, bias_max_share):
        excess = max(0.0, float(bias_max_share) - self.bias_threshold)
        denom = max(1e-6, 1.0 - self.bias_threshold)
        p = 1.0 - self.bias_lambda * excess / denom
        return float(np.clip(p, 0.5, 1.0))  # never below 0.5 for stability

    def compute(self, df):
        df = df.copy()

        # penalties and per-cluster deltas
        df["b"] = df["bias_max_share"].apply(self._bias_penalty)
        df["delta"] = df["sign"] * df["magnitude"] * df["reliability"] * df["b"]

        # aggregate daily by component (missing comps -> 0)
        comp = df.groupby(["date", "component"])["delta"].sum().unstack(fill_value=0.0).sort_index()

        # z-score normalization
        if self.rolling_days and len(comp) >= self.min_days_for_stats:
            mu = comp.rolling(self.rolling_days, min_periods=self.min_days_for_stats).mean().shift(1)
            sigma = comp.rolling(self.rolling_days, min_periods=self.min_days_for_stats).std().shift(1).replace(0, 1e-6)
            z = (comp - mu).div(sigma).fillna(0.0)
        else:
            mu = comp.mean()
            sigma = comp.std().replace(0, 1e-6)
            z = (comp - mu) / sigma

        # align weights to what's present
        w = pd.Series(self.weights)
        w = w.reindex(z.columns, fill_value=0.0)

        Z = (z * w).sum(axis=1)
        HI = (100 * np.tanh(self.alpha * Z)).round().astype(int)

        out = []
        for d, h in HI.items():
            ds = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
            out.append({"date": ds, "HI": int(h)})
        return out
