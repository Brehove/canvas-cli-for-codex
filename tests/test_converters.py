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


class ConverterListRegressionTests(unittest.TestCase):
    def test_blank_lines_do_not_fragment_unordered_list(self):
        rendered = markdown_to_html("- First\n\n- Second\n\n- Third")
        self.assertEqual(rendered.count("<ul>"), 1)
        self.assertEqual(rendered.count("<li>"), 3)

    def test_blank_lines_do_not_fragment_ordered_list(self):
        rendered = markdown_to_html("1. First\n\n2. Second\n\n3. Third")
        self.assertEqual(rendered.count("<ol>"), 1)
        self.assertEqual(rendered.count("<li>"), 3)

    def test_prose_keeps_lists_separate(self):
        rendered = markdown_to_html("- First\n\nA paragraph.\n\n- Second")
        self.assertEqual(rendered.count("<ul>"), 2)
        self.assertIn("<p>A paragraph.</p>", rendered)

    def test_html_ordered_list_becomes_numbered_markdown(self):
        pulled = html_to_markdown("<ol><li>First</li><li>Second</li></ol>")
        self.assertIn("1. First", pulled)
        self.assertIn("2. Second", pulled)
        self.assertNotIn("- First", pulled)

    def test_html_unordered_list_remains_bulleted(self):
        pulled = html_to_markdown("<ul><li>First</li><li>Second</li></ul>")
        self.assertIn("- First", pulled)
        self.assertIn("- Second", pulled)

    def test_ordered_list_round_trip(self):
        source = "<ol><li><strong>First</strong></li><li>Second</li></ol>"
        rendered = markdown_to_html(html_to_markdown(source))
        self.assertEqual(rendered.count("<ol>"), 1)
        self.assertEqual(rendered.count("<li>"), 2)
        self.assertIn("<strong>First</strong>", rendered)

    def test_table_and_embed_preservation(self):
        source = (
            '<table><caption>Example</caption><tr><th scope="col">A</th></tr></table>'
            '<iframe src="https://example.edu/embed"></iframe>'
        )
        pulled = html_to_markdown(source)
        self.assertIn("<table>", pulled)
        self.assertIn("<iframe", pulled)
        rendered = markdown_to_html(pulled)
        self.assertIn("<caption>Example</caption>", rendered)
        self.assertIn('<iframe src="https://example.edu/embed"></iframe>', rendered)


if __name__ == "__main__":
    unittest.main()
