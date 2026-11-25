"""Suite B — Agent BlocklistManager (5 tests)."""
import pytest
from PIL import Image

from tracker.blocklist import BlocklistManager


def _mgr(*patterns):
    m = BlocklistManager()
    m.update(list(patterns))
    return m


def test_should_blur_matches_substring():
    m = _mgr("1password")
    assert m.should_blur("1Password — Unlock", "") is True


def test_should_blur_case_insensitive():
    m = _mgr("keepass")
    assert m.should_blur("KeePass 2", "") is True


def test_should_not_blur_no_match():
    m = _mgr("1password", "bitwarden")
    assert m.should_blur("Chrome - GitHub", "chrome") is False


def test_should_not_blur_empty_list():
    m = BlocklistManager()   # no patterns loaded
    assert m.should_blur("1Password", "1password") is False


def test_blur_image_changes_pixels():
    # Left half white, right half black — the boundary blurs to grey
    img = Image.new("RGB", (100, 100))
    for x in range(100):
        for y in range(100):
            img.putpixel((x, y), (255, 255, 255) if x < 50 else (0, 0, 0))
    m = _mgr("anything")
    blurred = m.blur_image(img)
    # Pixel at the boundary should be neither pure white nor pure black
    r, g, b = blurred.getpixel((50, 50))
    assert 0 < r < 255
