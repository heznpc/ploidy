"""Progress events + SSE plumbing for live debate streaming.

The MCP tool path returns one dict once the debate has fully converged.
That's fine for short solo runs but hides every intermediate phase of
``run_auto`` — users wait 20-60 seconds staring at a spinner and then
see everything at once.

This module factors the progress channel out:

- :class:`ProgressEvent` is the wire format (stable JSON schema).
- :func:`emit` is a tiny callback shim the service uses; it tolerates
  the ``None`` callback and wraps synchronous callables for convenience.
- :func:`sse_format` turns an event into a Server-Sent-Event frame.

The HTTP endpoint lives in ``server.py`` so it can pick up the shared
service + auth context.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from typing import Any

ProgressCallback = Callable[["ProgressEvent"], Awaitable[None]]


@dataclass
class ProgressEvent:
    """One event in the debate progress stream.

    ``type`` is a short stable string downstream clients switch on.
    ``data`` is arbitrary JSON-serialisable context for that event.
    """

    type: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


async def emit(callback: ProgressCallback | None, event_type: str, **data: Any) -> None:
    """Fire ``callback`` with a new ProgressEvent. No-op when callback is None.

    Exceptions inside the callback are suppressed — a broken listener must
    never break the underlying debate. We log-and-continue at the caller.
    """
    if callback is None:
        return
    try:
        await callback(ProgressEvent(type=event_type, data=dict(data)))
    except Exception:
        # Intentionally swallowed. The progress channel is best-effort;
        # a debate must not fail because a client disconnected mid-stream.
        pass


def sse_format(event: ProgressEvent) -> str:
    """Render a ProgressEvent as one text/event-stream frame."""
    payload = json.dumps(event.to_dict(), ensure_ascii=False, default=str)
    return f"event: {event.type}\ndata: {payload}\n\n"
