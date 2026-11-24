"""Application blocklist: fetch from server, check window, blur screenshot."""
import io
import logging
import threading

logger = logging.getLogger(__name__)


class BlocklistManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._patterns: list[str] = []

    def update(self, patterns: list[str]) -> None:
        with self._lock:
            self._patterns = [p.lower() for p in patterns if p.strip()]
        logger.info("Blocklist updated: %d pattern(s)", len(self._patterns))

    def should_blur(self, window_title: str, process_name: str = "") -> bool:
        if not self._patterns:
            return False
        text = (window_title + " " + process_name).lower()
        with self._lock:
            return any(p in text for p in self._patterns)

    def blur_image(self, img) -> "PIL.Image.Image":
        from PIL import ImageFilter
        return img.filter(ImageFilter.GaussianBlur(radius=25))


# Module-level singleton used by screenshot.py and sync.py
blocklist = BlocklistManager()
