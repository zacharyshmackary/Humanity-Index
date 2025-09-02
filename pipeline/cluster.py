# pipeline/cluster.py

"""
Simple title-based clustering.

Input:  a list of article dicts, each at least with {"title": "...", "domain": "...", ...}
Output: a list of clusters, where each cluster is a list of the original article dicts.

Clustering is greedy: the first title in a cluster is the reference; a new title joins the
first cluster whose reference passes a similarity threshold; otherwise it starts a new cluster.
"""

from difflib import SequenceMatcher


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def cluster_titles(items, threshold: float = 0.70):
    """
    Group *dict* items by title similarity.

    - items: iterable of dicts; each should have a "title" key.
    - threshold: similarity (0..1) to join an existing cluster.

    Returns: List[List[dict]]  (each inner list is a cluster of the original dicts)
    """
    clusters: list[list[dict]] = []

    for it in items:
        # be defensive: accept dicts only, skip empties
        if not isinstance(it, dict):
            # coerce into a dict with best-effort title
            it = {"title": str(it)}
        title = it.get("title") or ""
        if not title:
            # if there is no title, skip—can't cluster meaningfully
            continue

        placed = False
        for cluster in clusters:
            # compare to the first item's title in the cluster
            anchor_title = cluster[0].get("title", "")
            if _similar(title, anchor_title) >= threshold:
                cluster.append(it)
                placed = True
                break

        if not placed:
            clusters.append([it])

    return clusters
