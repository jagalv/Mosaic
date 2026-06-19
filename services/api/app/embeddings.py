"""Embedding seam for Milestone 3 retrieval.

One place that knows how to turn text into a 384-dim vector with
BAAI/bge-small-en-v1.5 (local, $0, no rate limits). Both the bulk embedder
(ingest/embed.py) and the query side (rag/retrieve.py) go through here so the
encoding can never drift between index time and query time.

bge retrieval asymmetry (load-bearing for recall — James's refinement):
  - PASSAGES are embedded plain.
  - QUERIES are embedded with bge's instruction prefix
    "Represent this sentence for searching relevant passages:".
Mismatching these is a classic, silent recall killer. Both sides L2-normalize so
a dot product is cosine similarity (our HNSW index uses vector_cosine_ops).

The model is loaded lazily and cached, so importing this module (and thus the
API) stays cheap — the ~130MB model only loads when something actually embeds.
"""

from functools import lru_cache

from app.config import get_settings

# The exact query instruction bge-small-en-v1.5 was trained with for retrieval.
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

# Embedding dimension (must match models.EMBEDDING_DIM and migration 0004).
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _model():
    # Imported here, not at module top, so torch/sentence-transformers load only
    # when embedding actually happens (keeps API startup + tests light).
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(get_settings().embedding_model)


def embed_passages(texts: list[str], batch_size: int = 64) -> list[list[float]]:
    """Embed chunk passages (no instruction prefix), L2-normalized."""
    if not texts:
        return []
    vecs = _model().encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vecs]


def embed_query(text: str) -> list[float]:
    """Embed a search query WITH bge's retrieval instruction, L2-normalized."""
    vec = _model().encode(
        QUERY_INSTRUCTION + text,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vec.tolist()
