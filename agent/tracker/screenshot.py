"""Screenshot capture using mss with SHA-256 integrity hash."""
import hashlib
import io
from datetime import datetime, timezone
from pathlib import Path

import mss
import mss.tools
from PIL import Image

from tracker.config import config


def capture() -> tuple[bytes, str, datetime]:
    """Capture the primary monitor, resize to max 1280×800.

    Returns (png_bytes, sha256_hex, captured_at).
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    img.thumbnail((1280, 800), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    sha256 = hashlib.sha256(data).hexdigest()
    return data, sha256, datetime.now(timezone.utc)


def save_to_spool(window_id: str, data: bytes) -> Path:
    spool = Path(config.spool_dir)
    spool.mkdir(parents=True, exist_ok=True)
    path = spool / f"{window_id}.png"
    path.write_bytes(data)
    return path
