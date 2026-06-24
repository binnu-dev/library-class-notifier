"""Pluggable text-embedding providers for lens B.

Lens B compares each problem sentence against patent abstracts by cosine
similarity, so we need *some* embedding. Two backends are offered:

* ``SentenceTransformerProvider`` — real semantic embeddings. Used when the
  ``sentence-transformers`` package is installed. This is the production path.
* ``HashingProvider`` — a dependency-free, deterministic fallback (hashed
  character n-gram bag-of-words). It is weaker semantically but lets the whole
  pipeline (and the tests) run with no model download and no network.

``get_provider`` picks one based on ``Settings.embedding_backend``:
``auto`` prefers sentence-transformers and silently falls back to hashing.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, Sequence


class EmbeddingProvider(Protocol):
    name: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


_TOKEN_RE = re.compile(r"[a-z0-9]+")


class HashingProvider:
    """Deterministic hashed bag-of-words embedding. No dependencies.

    Each token is hashed into a fixed-width vector. Crude, but stable and good
    enough to exercise the ranking path and to give a non-trivial signal when
    no model is available.
    """

    name = "hashing"

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _tokens(self, text: str) -> list[str]:
        words = _TOKEN_RE.findall(text.lower())
        # add char trigrams so morphologically-near words share dimensions
        grams: list[str] = list(words)
        for w in words:
            padded = f"^{w}$"
            grams.extend(padded[i:i + 3] for i in range(len(padded) - 2))
        return grams

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            for tok in self._tokens(text):
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dim
                sign = 1.0 if (h >> 8) & 1 else -1.0
                vec[idx] += sign
            vectors.append(vec)
        return vectors


class SentenceTransformerProvider:
    """Real semantic embeddings via the ``sentence-transformers`` package."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # lazy import

        self.name = f"sentence-transformers:{model_name}"
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        arr = self._model.encode(list(texts), normalize_embeddings=False)
        return [list(map(float, row)) for row in arr]


def get_provider(backend: str = "auto",
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
                 ) -> EmbeddingProvider:
    """Resolve a provider from a backend name.

    ``auto`` tries sentence-transformers first and falls back to hashing.
    """
    backend = (backend or "auto").lower()

    if backend in ("hashing", "hash", "fallback"):
        return HashingProvider()

    if backend in ("auto", "sentence-transformers", "st"):
        try:
            return SentenceTransformerProvider(model_name)
        except Exception as exc:  # noqa: BLE001 - any import/load failure
            if backend == "auto":
                print(f"[embeddings] sentence-transformers unavailable "
                      f"({exc!r}); falling back to hashing provider.")
                return HashingProvider()
            raise

    raise ValueError(f"Unknown embedding backend: {backend!r}")
