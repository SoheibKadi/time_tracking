"""Agent test conftest: mock heavy platform dependencies before any agent imports."""
import sys
from unittest.mock import MagicMock

# Prevent import errors for packages not installed in the test environment
for _mod in [
    "PyQt6", "PyQt6.QtWidgets", "PyQt6.QtGui", "PyQt6.QtCore",
    "mss", "mss.tools",
    "pynput", "pynput.keyboard", "pynput.mouse",
]:
    sys.modules.setdefault(_mod, MagicMock())
