import unittest

from app.server import render


class RenderTests(unittest.TestCase):
    def test_page_has_landmarks_and_heading(self):
        html = render("Home", "<p>x</p>")
        for fragment in ('<nav aria-label="Main">', "<main>", "<h1>Home</h1>"):
            self.assertIn(fragment, html)

    def test_title_is_escaped(self):
        self.assertIn("&lt;b&gt;", render("<b>", ""))


if __name__ == "__main__":
    unittest.main()
