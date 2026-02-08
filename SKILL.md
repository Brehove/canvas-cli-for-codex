---
name: canvas
description: Use the Canvas CLI to help faculty or staff pull, review, edit, and safely push Canvas LMS content (pages, assignments, discussions, rubrics, and submissions). Trigger when users ask to update course content, revise assignment instructions, adjust due dates/points, review student submissions, manage rubrics, or sync local markdown/yaml changes back to Canvas.
---

# Canvas Skill

Use this skill to operate the `canvas` CLI and manage Canvas course content with Codex.

## Core workflow

1. Identify course with `canvas courses` if needed.
2. Pull only the target content (`canvas pull ...`).
3. Edit local files while preserving frontmatter IDs.
4. Preview with `canvas push ... --dry-run`.
5. Push real changes only after confirmation.

## Key commands

```bash
# Discovery
canvas courses
canvas modules "COURSE"
canvas items "COURSE" "MODULE"
canvas rubrics "COURSE"

# Pull
canvas pull "COURSE" -a "Assignment Name"
canvas pull "COURSE" -p "Page Name"
canvas pull "COURSE" -m "Module Name"
canvas pull "COURSE" -d "Discussion Name"
canvas pull "COURSE" --rubrics
canvas pull "COURSE" -a "Assignment Name" --submissions ungraded --discussions

# Push (safe sequence)
canvas push -f "path/to/file.md" --dry-run
canvas push -f "path/to/file.md"
canvas push -m "ModuleName" --dry-run
canvas push -m "ModuleName"
```

## Guardrails

- Always offer `--dry-run` before any mutating command.
- Keep `canvas_id` fields in frontmatter/YAML.
- Confirm before real push to production courses.
- Prefer targeted updates (`--file`) over broad pushes when feasible.

## Local structure

- Routing is controlled by `.canvas-config.yaml` `course_folders` + `default_folder`.
- Standard course names become folders like `SP26-ENGL-101-codex-course`.
- Pulled content typically lands in `assignments/`, `pages/`, `discussions/`, `rubrics/`, `submissions/`.

## Playbooks

Use `references/faculty-playbooks.md` for common faculty/staff tasks and prompt patterns.
