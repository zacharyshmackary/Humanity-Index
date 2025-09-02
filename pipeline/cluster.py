# pipeline/cluster.py
def cluster_titles(items):
    """Return a list of titles from a list of article-like objects."""
    out = []
    for it in items:
        if isinstance(it, dict):
            t = (
                it.get("title")
                or it.get("Title")
                or it.get("titleEnglish")
                or ""
            )
        else:
            t = str(it)
        out.append(t)
    return out
