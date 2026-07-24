"""In-memory build-progress tracker.

Single-instance MVP store (same pattern as the E2B sandbox registry in
server/sandbox.py): the background generation task writes progress here as it
runs, and the frontend polls GET /api/apps/{id}/progress to read it. A
horizontally-scaled deployment would back this with Redis instead.
"""

import asyncio
from typing import Optional

_progress: dict[str, dict] = {}
_tasks: set[asyncio.Task] = set()


def set_progress(app_id: str, **fields) -> None:
    _progress.setdefault(app_id, {})
    _progress[app_id].update(fields)


def get_progress(app_id: str) -> Optional[dict]:
    return _progress.get(app_id)


def track_task(task: asyncio.Task) -> None:
    """Keeps a reference to a background task so it isn't garbage-collected mid-run."""
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
