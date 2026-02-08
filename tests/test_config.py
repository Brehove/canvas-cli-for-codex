import os
import tempfile
import unittest
from pathlib import Path

import yaml

from canvas_cli.config import get_course_folder, get_courses_dir, parse_course_info


class CanvasConfigTests(unittest.TestCase):
    def test_parse_course_info_standard_format(self):
        result = parse_course_info("2026SP-PHIL-123-001H-16W: AI and Ethics")
        self.assertEqual(result["semester"], "SP26")
        self.assertEqual(result["course_code"], "PHIL-123")

    def test_parse_course_info_nonstandard_format(self):
        result = parse_course_info("My Sandbox Course")
        self.assertEqual(result, {"semester": "", "course_code": ""})

    def test_get_courses_dir_uses_default_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".canvas-config.yaml").write_text(
                yaml.dump({
                    "canvas_url": "https://example.instructure.com",
                    "api_token": "token",
                    "default_folder": "faculty-courses",
                })
            )

            old_cwd = Path.cwd()
            os.chdir(root)
            try:
                self.assertEqual(get_courses_dir().resolve(), (root / "faculty-courses").resolve())
            finally:
                os.chdir(old_cwd)

    def test_get_courses_dir_supports_legacy_courses_dir_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".canvas-config.yaml").write_text(
                yaml.dump({
                    "canvas_url": "https://example.instructure.com",
                    "api_token": "token",
                    "courses_dir": "legacy-courses",
                })
            )

            old_cwd = Path.cwd()
            os.chdir(root)
            try:
                self.assertEqual(get_courses_dir().resolve(), (root / "legacy-courses").resolve())
            finally:
                os.chdir(old_cwd)

    def test_get_course_folder_prefix_word_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".canvas-config.yaml").write_text(
                yaml.dump({
                    "canvas_url": "https://example.instructure.com",
                    "api_token": "token",
                    "default_folder": "courses",
                    "course_folders": {
                        "HIST": "History",
                    },
                })
            )

            old_cwd = Path.cwd()
            os.chdir(root)
            try:
                # Should not match HIST inside CHIST.
                folder = get_course_folder(
                    "CHIST-101",
                    "2026SP-CHIST-101-001: Cross-History Methods",
                )
                self.assertEqual(
                    folder.resolve(),
                    (root / "courses" / "SP26-CHIST-101-codex-course").resolve(),
                )

                # Should match the explicit HIST prefix.
                folder = get_course_folder(
                    "HIST-101",
                    "2026SP-HIST-101-001: World History",
                )
                self.assertEqual(
                    folder.resolve(),
                    (root / "History" / "SP26-HIST-101-codex-course").resolve(),
                )
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
