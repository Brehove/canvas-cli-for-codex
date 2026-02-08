# Canvas LMS Integration

You have access to the `canvas` CLI tool for faculty/staff Canvas LMS workflows.

## Quick Reference

| Task | Command |
|------|---------|
| List courses | `canvas courses` |
| List modules | `canvas modules "COURSE-CODE"` |
| List rubrics | `canvas rubrics "COURSE-CODE"` |
| Pull module | `canvas pull "COURSE-CODE" -m "Module 1"` |
| Pull assignment | `canvas pull "COURSE-CODE" -a "1.5 Assignment"` |
| Pull with rubrics | `canvas pull "COURSE-CODE" --rubrics` |
| Pull submissions | `canvas pull "COURSE-CODE" -a "1.5" --submissions ungraded --discussions` |
| Push file | `canvas push -f "path/to/file.md"` |
| Push module | `canvas push -m "Module 1"` |
| Dry run | `canvas push -f "file.md" --dry-run` |

## Working Directory

Run canvas commands from a directory under `.canvas-config.yaml`. The CLI finds config by walking up from the current folder.

Routing rules from `.canvas-config.yaml`:

- Mapped prefixes go to configured folders (example: `ENGL -> English`)
- Unmapped courses go to `default_folder` (default: `courses`)
- Standard course names generate subfolders like `SP26-ENGL-101-codex-course`

## Recommended Workflow

When asked to change Canvas content:

1. Identify course/module/assignment precisely (`canvas courses`, `canvas modules`)
2. Pull targeted content (`canvas pull ...`)
3. Edit local markdown/yaml
4. Preview with `--dry-run`
5. Confirm before real push

## File Format

```markdown
---
canvas_id: 316993   # Required for pushing
title: 1.5 Assignment
due_at: '2026-01-26T06:59:59Z'
points_possible: 20.0
submission_types: [online_text_entry, online_upload]
rubric_id: 17172
---

Assignment body in markdown...
```

## Guardrails

1. Offer `--dry-run` before any mutating command.
2. Do not remove or change `canvas_id` unless explicitly asked.
3. Confirm before pushing to live course content.
