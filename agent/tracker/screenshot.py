"""Screenshot capture using mss with SHA-256 integrity hash.

Phase 3: captures all monitors (combined via mss.monitors[0]) when
CAPTURE_ALL_MONITORS=true (default). Blurs the image if the foreground
window matches the user's application blocklist.
"""
import hashlib
import io
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import mss
from PIL import Image

from tracker.config import config
from tracker.blocklist import blocklist

logger = logging.getLogger(__name__)


def capture() -> tuple[bytes, str, datetime]:
    """Capture monitor(s), resize to max 1280×800, apply blocklist blur.

    Returns (png_bytes, sha256_hex, captured_at).
    Raises RuntimeError if capture fails (e.g., Wayland, no permission).
    """
    # Check foreground window against blocklist before capturing
    window_title, process_name = _get_foreground()
    should_blur = blocklist.should_blur(window_title, process_name)

    with mss.mss() as sct:
        # monitors[0] is the full virtual desktop (all monitors combined)
        # monitors[1] is the primary monitor only
        monitor = sct.monitors[0] if config.capture_all_monitors else sct.monitors[1]
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    if should_blur:
        logger.info("Applying blocklist blur (window: %r)", window_title)
        img = blocklist.blur_image(img)

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


def _get_foreground() -> tuple[str, str]:
    """Non-fatal wrapper around platform_utils.get_foreground_window."""
    try:
        from tracker.platform_utils import get_foreground_window
        return get_foreground_window()
    except Exception:
        return "", ""
