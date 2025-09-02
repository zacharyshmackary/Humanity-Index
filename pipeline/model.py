import pandas as pd, numpy as np, yaml

class HIModel:
    def __init__(self, settings="settings.yaml"):
        cfg = yaml.safe_load(open(settings))
        self.alpha = cfg["alpha"]
        self.bias_threshold = cfg["bias_threshold"]
        self.bias_penalty = cfg["bias_penalty"]
        self.weights = cfg["components"]

    def compute(self, df):
        df = df.copy()
        df["b"] = np.where(df["bias_max_share"]>=self.bias_threshold, self.bias_penalty,1)
        df["delta"] = df["sign"]*df["magnitude"]*df["reliability"]*df["b"]
        comp = df.groupby(["date","component"])["delta"].sum().unstack(fill_value=0)
        mu, sigma = comp.mean(), comp.std().replace(0,1)
        z = (comp-mu)/sigma
        Z = (z*self.weights).sum(axis=1)
        HI = (100*np.tanh(self.alpha*Z)).astype(int)
        return [{"date":d.strftime("%Y-%m-%d"),"HI":int(h)} for d,h in HI.items()]
