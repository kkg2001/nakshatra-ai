from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

STOP = set(["a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "has", "have", "i", "in", "is", "it", "me", "my", "of", "on", "or", "so", "that", "the", "this", "to", "was", "what", "when", "will", "with", "you", "your", "do", "does", "should", "can", "about"])


def tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9']+", text.lower()) if t not in STOP]


@dataclass
class Chunk:
    label: str
    title: str
    source: str
    text: str
    score: float = 0.0


class KnowledgeBase:
    def __init__(self, directory: Path, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.chunks: list[Chunk] = []
        for f in sorted(Path(directory).glob("*.md")):
            for part in re.split(r"(?m)^## ", f.read_text(encoding="utf-8"))[1:]:
                title, _, body = part.partition("\n")
                self.chunks.append(Chunk("", title.strip(), f.stem, body.strip()))
        self._tok = [tokens(c.title + " " + c.title + " " + c.text) for c in self.chunks]
        n = max(len(self._tok), 1)
        self._avg = sum(map(len, self._tok)) / n
        df: dict[str, int] = {}
        for t in self._tok:
            for w in set(t):
                df[w] = df.get(w, 0) + 1
        self._idf = {w: math.log(1 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    def search(self, query: str, k: int = 3) -> list[Chunk]:
        q = tokens(query)
        scored = []
        for chunk, toks in zip(self.chunks, self._tok):
            s = 0.0
            for w in set(q):
                f = toks.count(w)
                if f:
                    s += self._idf.get(w, 0) * f * (self.k1 + 1) / (
                        f + self.k1 * (1 - self.b + self.b * len(toks) / self._avg))
            if s > 0:
                scored.append((s, chunk))
        scored.sort(key=lambda x: -x[0])
        return [Chunk(f"K{i}", c.title, c.source, c.text, round(s, 3))
                for i, (s, c) in enumerate(scored[:k], 1)]


@lru_cache(maxsize=1)
def get_kb() -> KnowledgeBase:
    from backend.app.config import KNOWLEDGE_DIR
    return KnowledgeBase(KNOWLEDGE_DIR)
