"""WebSocket connection manager and pending-update signalling.

The sync HTTP routes update `pending_updates` (a plain dict).
The async WebSocket handler polls it every few seconds and pushes
the full share-view payload to connected clients.
"""
from datetime import datetime, timezone


# Maps str(share_token) → datetime of last submitted window
pending_updates: dict[str, datetime] = {}


def mark_updated(share_token: str) -> None:
    pending_updates[share_token] = datetime.now(timezone.utc)
