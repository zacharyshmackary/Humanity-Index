import pandas as pd, numpy as np, yaml

class HIModel:
    def __init__(self, settings="settings.yaml"):
        cfg = yaml.safe_load(open(settings))

        # Scale knob for tanh output
        self.alpha = float(cfg["alpha"])

        # Bias penalty (smooth)
        self.bias_threshold = float(cfg["bias_threshold"])
        self.bias_lambda = float(cfg.get("bias_lambda", 0.6))  # 0..1

        # Component weights
        self.weights = dict(cfg["components"])

        # History settings
        hist = cfg.get("history", {})
        self.min_days_for_stats = int(hist.get("min_days_for_stats", 14))
        self.rolling_days = int(hist.get("rolling_days", 0))  # 0=off

    def _bias_penalty(self, bias_max_share):
        # Smooth penalty once share exceeds threshold
        excess = max(0.0, float(bias_max_share) - self.bias_threshold)
        p = 1.0 - self.bias_lambda * excess / max(1e-6, 1.0 - self.bias_threshold)
        return float(np.clip(p, 0.5, 1.0))  # never below 0.5 unless you want stronger

    def compute(self, df):
        df = df.copy()

        # penalty per row
        df["b"] = df["bias_max_share"].apply(self._bias_penalty)

        # per-cluster contribution
        df["delta"] = df["sign"] * df["magnitude"] * df["reliability"] * df["b"]

        # daily component totals
        comp = df.groupby(["date","component"])["delta"].sum().unstack(fill_value=0.0)

        # --- normalization to z-scores ---
        comp = comp.sort_index()  # ensure ascending by date

        if self.rolling_days and len(comp) >= self.min_days_for_stats:
            # Rolling mean/std, using prior window (shift by 1 to avoid lookahead)
            mu = comp.rolling(self.rolling_days, min_periods=self.min_days_for_stats).mean().shift(1)
            sigma = comp.rolling(self.rolling_days, min_periods=self.min_days_for_stats).std().shift(1).replace(0, 1e-6)
            z = (comp - mu).div(sigma)
            z = z.fillna(0.0)  # for early days without enough history
        else:
            mu, sigma = comp.mean(), comp.std().replace(0, 1e-6)
            z = (comp - mu) / sigma

        # align weights to available columns
        w = pd.Series(self.weights)
        w = w.reindex(z.columns, fill_value=0.0)

        Z = (z * w).sum(axis=1)
        HI = (100 * np.tanh(self.alpha * Z)).round().astype(int)

        # back to list of dicts
        out = []
        for d, h in HI.items():
            ds = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
            out.append({"date": ds, "HI": int(h)})
        return out
