import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml
from click.testing import CliRunner
from canvas_cli.api import CanvasAPI
from canvas_cli.cli import cli, push_file, save_assignment, convert_rubric_to_canvas_format


class ImprovementsTests(unittest.TestCase):
    def test_rubric_form_encoding_and_association(self):
        api = CanvasAPI('https://example.edu', 'test')
        api._post = Mock(return_value={})
        api.create_rubric(1, title='Example', criteria={'0': {'ignore_for_scoring': True}},
                          rubric_association={'association_id': 2, 'use_for_grading': False})
        args = api._post.call_args.kwargs
        self.assertIn(('rubric[criteria][0][ignore_for_scoring]', 'true'), args['data'])
        self.assertIn(('rubric_association[use_for_grading]', 'false'), args['data'])
        self.assertEqual(args['headers']['Content-Type'], 'application/x-www-form-urlencoded')

    def test_checkpoint_mutations_and_errors(self):
        api = CanvasAPI('https://example.edu', 'test')
        response = Mock()
        response.json.return_value = {'data': {'updateDiscussionTopic': {'discussionTopic': {'_id': '2'}}}}
        api.session.post = Mock(return_value=response)
        api.update_checkpoints(2, [{'tag': 'reply_to_entry', 'points_possible': 3,
                                   'due_at': None, 'replies_required': 2}])
        payload = api.session.post.call_args.kwargs['json']['variables']['input']
        self.assertTrue(payload['setCheckpoints'])
        self.assertEqual(payload['checkpoints'][0]['repliesRequired'], 2)
        api.disable_checkpoints(2)
        self.assertFalse(api.session.post.call_args.kwargs['json']['variables']['input']['setCheckpoints'])
        response.json.return_value = {'errors': [{'message': 'Invalid'}]}
        with self.assertRaisesRegex(Exception, 'GraphQL errors'):
            api.disable_checkpoints(2)

    def test_dates_checkpoints_and_dry_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '_course.yaml').write_text('canvas_id: 1\n')
            path = root / 'discussion.md'
            path.write_text('''---
canvas_id: 2
discussion_topic_id: 3
submission_types: [discussion_topic]
unlock_at: 2026-10-20T10:00:00Z
checkpoints:
  - tag: reply_to_topic
    points_possible: 5
    due_at: 2026-10-22T10:00:00Z
---
Hello
''')
            api = Mock()
            self.assertTrue(push_file(api, path, dry_run=True))
            self.assertEqual(api.mock_calls, [])
            push_file(api, path)
            self.assertEqual(api.update_assignment.call_args.kwargs['unlock_at'], '2026-10-20T10:00:00Z')
            self.assertEqual(api.update_checkpoints.call_args.args[1][0]['due_at'], '2026-10-22T10:00:00Z')

    def test_full_pull_retains_orphans_and_distinguishes_object_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'custom.md').write_text('---\ncanvas_id: 7\ncanvas_url: intro\n---\nOld')
            api = Mock()
            api.get_course.return_value = {'id': 1, 'name': 'Course'}
            api.get_modules.return_value = [{'id': 10, 'name': 'Module 1'}]
            api.get_module_items.return_value = [
                {'type': 'Page', 'page_url': 'intro'}, {'type': 'Assignment', 'content_id': 7}]
            api.get_pages.return_value = [{'url': 'intro'}, {'url': 'orphan'}]
            api.get_page.side_effect = lambda _, url: {'page_id': 7 if url == 'intro' else 8,
                                                      'url': url, 'title': url, 'body': '<p>New</p>'}
            api.get_assignments.return_value = [
                {'id': 7, 'name': 'Task', 'submission_types': ['online_text_entry']},
                {'id': 9, 'name': 'Outside', 'submission_types': ['online_text_entry']}]
            with patch('canvas_cli.cli.get_api', return_value=api), patch('canvas_cli.cli.get_course_folder', return_value=root):
                result = CliRunner().invoke(cli, ['pull', '1'])
            self.assertEqual(result.exit_code, 0, result.output + str(result.exception))
            self.assertIn('New', (root / 'custom.md').read_text())
            self.assertTrue((root / 'Module-1/Task.md').exists())
            self.assertTrue((root / 'pages/orphan.md').exists())
            self.assertTrue((root / 'assignments/Outside.md').exists())
            api.get_submissions.assert_not_called()

    def test_authenticated_attachment_download_preserved(self):
        from canvas_cli.cli import save_submission
        with tempfile.TemporaryDirectory() as folder:
            api = Mock()
            api.session.get.return_value.content = b'example'
            save_submission(Path(folder), 'Task', {'attachments': [
                {'url': 'https://example.edu/file', 'filename': 'example.txt'}]},
                {'id': 1, 'name': 'Example'}, api=api)
            api.session.get.assert_called_once_with('https://example.edu/file', timeout=30)


if __name__ == '__main__':
    unittest.main()
