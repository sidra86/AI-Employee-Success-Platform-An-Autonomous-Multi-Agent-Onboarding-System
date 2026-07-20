"""Mock email notification tool."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, List

from tools.base import BaseTool

# In-memory outbox for demo / dashboard visibility
EMAIL_OUTBOX: List[dict] = []


class MockEmailTool(BaseTool):
    name = "mock_email"
    description = "Send a mock email notification (logged to outbox, not actually emailed)"

    def run(
        self,
        to: str,
        subject: str,
        body: str,
        **_: Any,
    ) -> str:
        message = {
            "to": to,
            "subject": subject,
            "body": body,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "mock_sent",
        }
        EMAIL_OUTBOX.insert(0, message)
        if len(EMAIL_OUTBOX) > 100:
            del EMAIL_OUTBOX[100:]
        return json.dumps(message)
