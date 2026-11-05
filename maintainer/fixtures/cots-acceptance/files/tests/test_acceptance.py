"""Acceptance tests for the vendor's csvsum 4.2, one per requirement in REQUIREMENTS.md."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CSVSUM = Path(__file__).resolve().parent.parent / "vendor" / "csvsum" / "csvsum.py"


def csvsum(text, column="amount"):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "input.csv"
        path.write_text(text, encoding="utf-8")
        result = subprocess.run([sys.executable, str(CSVSUM), "--column", column, str(path)],
                                capture_output=True, text=True, check=True)
    return result.stdout.strip()


class AcceptanceTests(unittest.TestCase):
    def test_req1_sums_column(self):
        self.assertEqual(csvsum("id,amount\n1,10\n2,32\n"), "42")

    def test_req2_skips_header(self):
        self.assertEqual(csvsum("amount\n5\n"), "5")

    def test_req3_thousands_separators(self):
        self.assertEqual(csvsum('id,amount\n1,"1,234"\n2,"2,000"\n'), "3234")


if __name__ == "__main__":
    unittest.main()
