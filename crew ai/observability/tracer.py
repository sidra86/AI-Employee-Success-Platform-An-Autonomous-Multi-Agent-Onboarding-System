"""
Lightweight in-process + DB-ready execution tracer for agent workflows.
"""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional


@dataclass
class TraceSpan:
    span_id: str
    name: str
    kind: str  # agent | tool | workflow | evaluator | planner
    started_at: float
    ended_at: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "running"
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_usage: Dict[str, int] = field(default_factory=dict)
    children: List["TraceSpan"] = field(default_factory=list)

    def finish(self, status: str = "ok", error: Optional[str] = None, **extra: Any) -> None:
        self.ended_at = time.time()
        self.duration_ms = round((self.ended_at - self.started_at) * 1000, 2)
        self.status = status
        self.error = error
        if extra:
            self.metadata.update(extra)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


class ExecutionTracer:
    """Collects nested spans for a single onboarding workflow run."""

    def __init__(self, workflow_name: str = "onboarding", employee_id: Optional[int] = None):
        self.trace_id = str(uuid.uuid4())
        self.workflow_name = workflow_name
        self.employee_id = employee_id
        self.created_at = datetime.utcnow().isoformat()
        self.root = TraceSpan(
            span_id=str(uuid.uuid4()),
            name=workflow_name,
            kind="workflow",
            started_at=time.time(),
        )
        self._stack: List[TraceSpan] = [self.root]
        self.events: List[Dict[str, Any]] = []

    def log(self, message: str, level: str = "info", **meta: Any) -> None:
        self.events.append(
            {
                "ts": datetime.utcnow().isoformat(),
                "level": level,
                "message": message,
                "span": self._stack[-1].name if self._stack else None,
                **meta,
            }
        )

    @contextmanager
    def span(
        self,
        name: str,
        kind: str = "agent",
        **metadata: Any,
    ) -> Generator[TraceSpan, None, None]:
        child = TraceSpan(
            span_id=str(uuid.uuid4()),
            name=name,
            kind=kind,
            started_at=time.time(),
            metadata=dict(metadata),
        )
        parent = self._stack[-1]
        parent.children.append(child)
        self._stack.append(child)
        self.log(f"Started {kind}: {name}", kind=kind)
        try:
            yield child
            if child.status == "running":
                child.finish(status="ok")
            self.log(f"Finished {kind}: {name}", kind=kind, duration_ms=child.duration_ms)
        except Exception as exc:
            child.finish(status="error", error=str(exc))
            self.log(f"Error in {kind}: {name}: {exc}", level="error", kind=kind)
            raise
        finally:
            if self._stack and self._stack[-1] is child:
                self._stack.pop()

    def record_tokens(self, prompt: int = 0, completion: int = 0, total: Optional[int] = None) -> None:
        span = self._stack[-1]
        usage = {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": total if total is not None else prompt + completion,
        }
        for k, v in usage.items():
            span.token_usage[k] = span.token_usage.get(k, 0) + v

    def estimate_tokens_from_text(self, text: str) -> int:
        # Rough heuristic ~4 chars/token
        return max(1, len(text or "") // 4)

    def finish(self, status: str = "ok", error: Optional[str] = None) -> Dict[str, Any]:
        if self.root.status == "running":
            self.root.finish(status=status, error=error)
        return self.summary()

    def summary(self) -> Dict[str, Any]:
        flat = self._flatten(self.root)
        total_tokens = sum(s.token_usage.get("total_tokens", 0) for s in flat)
        tools_used = [s.name for s in flat if s.kind == "tool"]
        agents_run = [s.name for s in flat if s.kind == "agent"]
        errors = [s for s in flat if s.status == "error"]
        return {
            "trace_id": self.trace_id,
            "workflow": self.workflow_name,
            "employee_id": self.employee_id,
            "created_at": self.created_at,
            "status": self.root.status,
            "duration_ms": self.root.duration_ms,
            "agents_run": agents_run,
            "tools_used": tools_used,
            "total_tokens_estimate": total_tokens,
            "error_count": len(errors),
            "execution_order": [s.name for s in flat if s.kind in ("agent", "tool", "planner", "evaluator")],
            "events": self.events[-100:],
            "tree": self.root.to_dict(),
        }

    def _flatten(self, span: TraceSpan) -> List[TraceSpan]:
        items = [span]
        for child in span.children:
            items.extend(self._flatten(child))
        return items


# Process-wide recent traces for dashboard (ring buffer)
_RECENT_TRACES: List[Dict[str, Any]] = []
_MAX_TRACES = 100


def store_trace(summary: Dict[str, Any]) -> None:
    _RECENT_TRACES.insert(0, summary)
    if len(_RECENT_TRACES) > _MAX_TRACES:
        del _RECENT_TRACES[_MAX_TRACES:]


def get_recent_traces(limit: int = 20) -> List[Dict[str, Any]]:
    return _RECENT_TRACES[:limit]


def get_tracer(workflow_name: str = "onboarding", employee_id: Optional[int] = None) -> ExecutionTracer:
    return ExecutionTracer(workflow_name=workflow_name, employee_id=employee_id)
