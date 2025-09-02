import re

RULES = [
    ("A", -1, r"war|attack|missile|drone|conflict|clashes|shooting|airstrike|invasion|terror|raid|shelling"),
    ("C", -1, r"earthquake|flood|wildfire|hurricane|cyclone|landslide|eruption|famine|outbreak"),
    ("D", +1, r"court|verdict|rights|anti[- ]corruption|transparency|accountability|treaty|ceasefire"),
    ("E", +1, r"vaccine|cancer|science|research|discovery|breakthrough|trial|approved|cure|space|fusion"),
    ("B", +1, r"aid|donation|charity|volunteer|rebuild|peace|reconciliation|humanitarian|rescued|relief"),
]
STRONG_WORDS = re.compile(r"\b(major|massive|deadly|historic|record|breakthrough|landmark|devastating)\b", re.I)
COMPILED = [(c, s, re.compile(p, re.I)) for (c, s, p) in RULES]

def categorize(title: str):
    for comp, sign, patt in COMPILED:
        if patt.search(title):
            strong = len(STRONG_WORDS.findall(title))
            mag = 0.6 + 0.1*strong
            return comp, sign, max(0.3, min(1.0, mag))
    return "D", +1, 0.3
