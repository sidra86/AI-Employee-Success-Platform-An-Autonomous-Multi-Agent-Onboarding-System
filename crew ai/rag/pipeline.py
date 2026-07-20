"""
RAG pipeline: ingest PDFs/text into the vector store and retrieve context for agents.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from rag.chunker import chunk_text
from rag.pdf_loader import extract_text_from_pdf
from vector_store.chroma_store import get_vector_store

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")


class RAGPipeline:
    """Ingest and retrieve onboarding knowledge documents."""

    def __init__(self):
        self.store = get_vector_store()
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    def ingest_pdf(
        self,
        file_bytes: bytes,
        filename: str,
        category: str = "general",
        title: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        text = extract_text_from_pdf(file_bytes)
        return self.ingest_text(
            text=text,
            filename=filename,
            category=category,
            title=title or filename,
            document_id=document_id,
            source_type="pdf",
        )

    def ingest_text(
        self,
        text: str,
        filename: str,
        category: str = "general",
        title: Optional[str] = None,
        document_id: Optional[str] = None,
        source_type: str = "text",
    ) -> Dict[str, Any]:
        document_id = document_id or str(uuid.uuid4())
        chunks = chunk_text(text)
        if not chunks:
            return {
                "document_id": document_id,
                "filename": filename,
                "chunk_count": 0,
                "status": "empty",
            }

        # Persist raw upload
        safe_name = f"{document_id}_{os.path.basename(filename)}"
        path = os.path.join(UPLOAD_DIR, safe_name)
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(text)

        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "title": title or filename,
                "category": category,
                "chunk_index": i,
                "source_type": source_type,
                "uploaded_at": datetime.utcnow().isoformat(),
            }
            for i in range(len(chunks))
        ]
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        self.store.add_texts(chunks, metadatas=metadatas, ids=ids)

        return {
            "document_id": document_id,
            "filename": filename,
            "title": title or filename,
            "category": category,
            "chunk_count": len(chunks),
            "backend": self.store.backend,
            "status": "indexed",
            "storage_path": path,
        }

    def retrieve(
        self,
        query: str,
        k: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        where = {"category": category} if category else None
        return self.store.similarity_search(query=query, k=k, where=where)

    def build_context(
        self,
        query: str,
        k: int = 5,
        category: Optional[str] = None,
    ) -> str:
        hits = self.retrieve(query, k=k, category=category)
        if not hits:
            return "No relevant knowledge base documents found."
        parts = []
        for i, hit in enumerate(hits, 1):
            meta = hit.get("metadata") or {}
            source = meta.get("title") or meta.get("filename") or "unknown"
            cat = meta.get("category", "general")
            parts.append(f"[{i}] ({cat} | {source})\n{hit.get('content', '')}")
        return "\n\n---\n\n".join(parts)

    def delete_document(self, document_id: str) -> int:
        return self.store.delete_by_document_id(document_id)

    def stats(self) -> Dict[str, Any]:
        return {
            "chunk_count": self.store.count(),
            "backend": self.store.backend,
            "upload_dir": UPLOAD_DIR,
        }


_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline
