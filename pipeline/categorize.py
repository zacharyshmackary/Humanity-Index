import re

# Very simple keyword-based categorizer. You can expand this anytime.
RULES = [
    # component, sign, keywords
    ("A", -1, r"war|attack|missile|drone|conflict|clashes|shooting|airstrike|invasion|terror|raid|shelling"),
    ("C", -1, r"earthquake|flood|wildfire|hurricane|cyclone|landslide|eruption|famine|outbreak|collapse"),
    ("D", +1, r"court|verdict|rights|anti[- ]corruption|transparency|accountability|treaty|ceasefire"),
    ("E", +1, r"vaccine|cancer|science|research|discovery|breakthrough|trial|approved|cure|space|fusion"),
    ("B", +1, r"aid|donation|charity|volunteer|rebuild|peace|reconciliation|humanitarian|rescued|relief"),
]

_compiled = [(c, s, re.compile(pat, re.I)) for (c, s, pat) in RULES]

def categorize(title):
    for comp, sign, pat in _compiled:
        if pat.search(title):
            # magnitude heuristic: stronger words → bigger magnitude
            strong = len(re.findall(r"\b(major|massive|deadly|historic|record|breakthrough|landmark)\b", title, re.I))
            mag = 0.6 + 0.1*strong
            mag = max(0.3, min(1.0, mag))
            return comp, sign, mag
    # fallback: neutral small magnitude, treated as slightly positive civics
    return "D", +1, 0.3
