from __future__ import annotations

import re
from typing import List, Tuple

from .coordinator import TurnResult


def _tokenize(s: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", s.lower()))


def summarize(results: List[TurnResult]) -> Tuple[str, float]:
    """Return a brief synthesis and a naive disagreement score."""
    texts = [r.text for r in results if r.text]
    if not texts:
        return ("No responses.", 0.0)
    vocab = [_tokenize(t) for t in texts]
    inter = set.intersection(*vocab) if len(vocab) > 1 else vocab[0]
    union = set.union(*vocab) if len(vocab) > 1 else vocab[0]
    jaccard = len(inter) / max(1, len(union))
    disagreement = 1.0 - jaccard
    points = list(inter)[:5]
    synthesis = "Agreements: " + (", ".join(points) if points else "(few)")
    return (synthesis, round(disagreement, 2))

