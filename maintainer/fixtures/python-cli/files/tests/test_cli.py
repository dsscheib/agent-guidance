import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from wc_cli.cli import count_words, main, summarize


class CountTests(unittest.TestCase):
    def test_counts_words_across_lines(self):
        self.assertEqual(count_words("one two\nthree"), 3)

    def test_summary(self):
        self.assertEqual(summarize("a b\n"), {"lines": 1, "words": 2, "chars": 4})

    def test_main_prints_counts_for_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("hello world\n", encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main([str(path)]), 0)
        self.assertEqual(out.getvalue().strip(), f"1 2 12 {path}")


if __name__ == "__main__":
    unittest.main()
