"""Regression for the one-off contrast check used on 2026-10-25 (scripts/check-contrast-once.py)."""
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check-contrast-once.py"


class ContrastOnceTests(unittest.TestCase):
    def test_prints_the_dark_theme_colors(self):
        out = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, check=True).stdout
        self.assertIn("#e0e0e0 on #1e1e1e", out)


if __name__ == "__main__":
    unittest.main()
