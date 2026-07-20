"""
ChromaDB-backed vector store with a lightweight local embedding fallback.

Works without OpenAI. Uses a deterministic bag-of-words embedding when
sentence-transformers / OpenAI embeddings are unavailable.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "onboarding_knowledge")


class LocalHashEmbedding:
    """Deterministic local embedding for offline / demo environments."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9]{2,}", (text or "").lower())

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = self._tokenize(text)
        if not tokens:
            return vec
        for tok in tokens:
            digest = hashlib.md5(tok.encode("utf-8")).hexdigest()
            idx = int(digest[:8], 16) % self.dim
            sign = 1.0 if int(digest[8:10], 16) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class ChromaVectorStore:
    """Thin wrapper around ChromaDB for onboarding knowledge documents."""

    def __init__(self, persist_directory: str = PERSIST_DIR, collection_name: str = COLLECTION_NAME):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding = LocalHashEmbedding()
        self._client = None
        self._collection = None
        self._memory_docs: List[Dict[str, Any]] = []
        self._backend = "memory"
        self._init_store()

    def _init_store(self) -> None:
        os.makedirs(self.persist_directory, exist_ok=True)
        try:
            import chromadb
            from chromadb.config import Settings

            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._backend = "chromadb"
        except Exception:
            # Graceful fallback when chromadb is not installed
            self._backend = "memory"
            self._memory_docs = []

    @property
    def backend(self) -> str:
        return self._backend

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        if not texts:
            return []
        ids = ids or [str(uuid.uuid4()) for _ in texts]
        metadatas = metadatas or [{} for _ in texts]
        embeddings = self.embedding.embed_documents(texts)

        if self._backend == "chromadb" and self._collection is not None:
            self._collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        else:
            for i, text, meta, emb in zip(ids, texts, metadatas, embeddings):
                self._memory_docs.append(
                    {"id": i, "document": text, "metadata": meta, "embedding": emb}
                )
        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        query_emb = self.embedding.embed_query(query)

        if self._backend == "chromadb" and self._collection is not None:
            kwargs: Dict[str, Any] = {
                "query_embeddings": [query_emb],
                "n_results": max(k, 1),
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                kwargs["where"] = where
            try:
                results = self._collection.query(**kwargs)
            except Exception:
                results = self._collection.query(
                    query_embeddings=[query_emb],
                    n_results=max(k, 1),
                    include=["documents", "metadatas", "distances"],
                )
            docs: List[Dict[str, Any]] = []
            for i, doc in enumerate(results.get("documents", [[]])[0]):
                docs.append(
                    {
                        "content": doc,
                        "metadata": (results.get("metadatas") or [[]])[0][i] or {},
                        "distance": (results.get("distances") or [[]])[0][i]
                        if results.get("distances")
                        else None,
                        "id": (results.get("ids") or [[]])[0][i]
                        if results.get("ids")
                        else None,
                    }
                )
            return docs

        # In-memory cosine similarity fallback
        scored = []
        for item in self._memory_docs:
            if where:
                meta = item.get("metadata") or {}
                if any(meta.get(k) != v for k, v in where.items()):
                    continue
            score = self._cosine(query_emb, item["embedding"])
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "content": item["document"],
                "metadata": item.get("metadata") or {},
                "distance": 1 - score,
                "id": item["id"],
            }
            for score, item in scored[:k]
        ]

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def count(self) -> int:
        if self._backend == "chromadb" and self._collection is not None:
            return self._collection.count()
        return len(self._memory_docs)

    def delete_by_document_id(self, document_id: str) -> int:
        if self._backend == "chromadb" and self._collection is not None:
            existing = self._collection.get(where={"document_id": document_id})
            ids = existing.get("ids") or []
            if ids:
                self._collection.delete(ids=ids)
            return len(ids)
        before = len(self._memory_docs)
        self._memory_docs = [
            d for d in self._memory_docs if (d.get("metadata") or {}).get("document_id") != document_id
        ]
        return before - len(self._memory_docs)


_store: Optional[ChromaVectorStore] = None


def get_vector_store() -> ChromaVectorStore:
    global _store
    if _store is None:
        _store = ChromaVectorStore()
    return _store
