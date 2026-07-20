"""Knowledge / RAG related tools."""

from __future__ import annotations

import json
from typing import Any, Optional

from tools.base import BaseTool


class KnowledgeSearchTool(BaseTool):
    name = "knowledge_search"
    description = "Semantic search across the onboarding knowledge base (RAG)"

    def run(self, query: str, k: int = 5, category: Optional[str] = None, **_: Any) -> str:
        from rag.pipeline import get_rag_pipeline

        hits = get_rag_pipeline().retrieve(query=query, k=int(k), category=category)
        return json.dumps({"query": query, "results": hits, "count": len(hits)})


class DocumentRetrievalTool(BaseTool):
    name = "document_retrieval"
    description = "Retrieve grounded context snippets from uploaded onboarding documents"

    def run(self, query: str, k: int = 4, category: Optional[str] = None, **_: Any) -> str:
        from rag.pipeline import get_rag_pipeline

        context = get_rag_pipeline().build_context(query=query, k=int(k), category=category)
        return context


class PolicyAccessTool(BaseTool):
    name = "policy_access"
    description = "Access company policies from the knowledge base (HR, compliance, handbook)"

    def run(self, topic: str = "company policy", **_: Any) -> str:
        from rag.pipeline import get_rag_pipeline

        context = get_rag_pipeline().build_context(
            query=topic,
            k=5,
            category=None,
        )
        # Prefer policy/hr categories when available
        policy_hits = get_rag_pipeline().retrieve(query=topic, k=3, category="policy")
        hr_hits = get_rag_pipeline().retrieve(query=topic, k=3, category="hr")
        if policy_hits or hr_hits:
            from rag.pipeline import get_rag_pipeline as grp

            parts = []
            for hit in (policy_hits + hr_hits)[:5]:
                meta = hit.get("metadata") or {}
                parts.append(f"[{meta.get('category', 'policy')}] {hit.get('content', '')}")
            return "\n\n".join(parts) if parts else context
        return context
