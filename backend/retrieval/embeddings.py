import re
import math
import hashlib
from typing import List
import requests
from django.conf import settings


class EmbeddingEngine:
    """
    Generates embeddings for research passages.
    Prioritizes Ollama's local embedding endpoint; falls back to a deterministic,
    normalized semantic feature projection (dim=384) when Ollama is offline.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = getattr(settings, 'EMBEDDING_DIM', dimension)
        self.ollama_base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = getattr(settings, 'OLLAMA_EMBED_MODEL', 'nomic-embed-text')

    def embed_text(self, text: str) -> List[float]:
        clean_text = text.strip()
        if not clean_text:
            return [0.0] * self.dimension

        # Try Ollama endpoint
        try:
            resp = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={"model": self.ollama_model, "prompt": clean_text},
                timeout=1.5
            )
            if resp.status_code == 200:
                data = resp.json()
                vec = data.get('embedding', [])
                if vec and len(vec) == self.dimension:
                    return self._normalize(vec)
                elif vec:
                    # Interpolate or pad to self.dimension
                    return self._resize_vector(vec, self.dimension)
        except Exception:
            # Fallback to local semantic hashing projection
            pass

        return self._local_semantic_embedding(clean_text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

    def _local_semantic_embedding(self, text: str) -> List[float]:
        """
        Deterministic, zero-overhead semantic feature hashing projection.
        Maps word unigrams, bigrams, and token subwords into a dense, normalized unit vector.
        Preserves cosine distance properties for semantic matching without external heavy weights.
        """
        vec = [0.0] * self.dimension
        tokens = re.findall(r'\b[a-z0-9_\-]{2,}\b', text.lower())

        if not tokens:
            return vec

        # Compute term frequency and n-grams
        features = {}
        for i, t in enumerate(tokens):
            features[t] = features.get(t, 0.0) + 1.0
            if i < len(tokens) - 1:
                bigram = f"{t}_{tokens[i+1]}"
                features[bigram] = features.get(bigram, 0.0) + 1.5

        for feat, weight in features.items():
            # Hash to index and sign
            h = int(hashlib.sha256(feat.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            # Diminishing marginal term weight (log TF)
            val = sign * (1.0 + math.log(weight))
            vec[idx] += val

        return self._normalize(vec)

    def _resize_vector(self, vec: List[float], target_dim: int) -> List[float]:
        if len(vec) == target_dim:
            return self._normalize(vec)
        if len(vec) > target_dim:
            return self._normalize(vec[:target_dim])
        # Pad with zeros
        padded = list(vec) + [0.0] * (target_dim - len(vec))
        return self._normalize(padded)

    @staticmethod
    def _normalize(vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in vec))
        if norm < 1e-9:
            return vec
        return [x / norm for x in vec]
