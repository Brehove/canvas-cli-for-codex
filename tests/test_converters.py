import unittest

from canvas_cli.converters import html_to_markdown, markdown_to_html


class ConverterTests(unittest.TestCase):
    def test_html_table_is_preserved_in_markdown(self):
        html = "<p>Intro</p><table><tr><th scope=\"col\">H</th></tr><tr><td>A</td></tr></table><p>End</p>"
        md = html_to_markdown(html)
        self.assertIn("<table>", md)
        self.assertIn("scope=\"col\"", md)

    def test_markdown_table_html_passthrough(self):
        md = "Start\n\n<table><thead><tr><th scope=\"col\">H</th></tr></thead><tbody><tr><td>A</td></tr></tbody></table>\n\nEnd"
        html = markdown_to_html(md)
        self.assertIn("<table>", html)
        self.assertIn("scope=\"col\"", html)


if __name__ == "__main__":
    unittest.main()
