from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def cluster_titles(items, threshold=0.28, max_clusters=150):
    """
    items: list of {'title','url','domain','date'}
    returns: list of clusters (each cluster is a list of those dicts)
    """
    if not items:
        return []

    titles = [it["title"] for it in items]
    vec = TfidfVectorizer(stop_words="english", max_features=5000, ngram_range=(1, 2))
    X = vec.fit_transform(titles)
    S = cosine_similarity(X)

    n = len(items)
    used = np.zeros(n, dtype=bool)
    clusters = []

    for i in range(n):
        if used[i]:
            continue
        members = list(np.where(S[i] >= threshold)[0])
        for m in members:
            used[m] = True
        clusters.append([items[j] for j in members])
        if len(clusters) >= max_clusters:
            break
    return clusters
