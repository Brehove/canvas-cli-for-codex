# Canvas CLI

A command-line tool for faculty and staff to pull and push Canvas LMS course content as local Markdown/YAML files. It is designed to work well with Codex CLI so you can ask Codex to help edit course materials safely before publishing.

## What This Solves

- Pull pages, assignments, discussions, rubrics, and submissions from Canvas
- Edit content locally with full YAML frontmatter metadata
- Push only what you intend, with `--dry-run` previews first
- Use Codex to draft, revise, and QA course content before syncing

## Quick Start

```bash
# 1) Clone into Codex skills
mkdir -p ~/.codex/skills
git clone <repo-url> ~/.codex/skills/canvas

# 2) Install
pip install -e ~/.codex/skills/canvas

# 3) Create a working folder for your term
mkdir -p ~/canvas-work/spring-2026
cd ~/canvas-work/spring-2026

# 4) Configure Canvas access
canvas config
# Prompts for Canvas URL and API token

# 5) Verify access
canvas courses
```

Create a Canvas token from **Account -> Settings -> New Access Token**.

## Faculty Workflows (Codex + Canvas)

### 1) Update one assignment

```bash
canvas pull "ENGL-101" -a "Essay 1"
```

Ask Codex: "Revise this assignment for clarity, keep points and due date the same."

Preview and push:

```bash
canvas push -f "English/SP26-ENGL-101-codex-course/assignments/Essay-1.md" --dry-run
canvas push -f "English/SP26-ENGL-101-codex-course/assignments/Essay-1.md"
```

### 2) Update a module page set

```bash
canvas pull "PHIL-123" -m "Module 2"
canvas push -m "Module-2" --dry-run
canvas push -m "Module-2"
```

### 3) Pull ungraded submissions for feedback

```bash
canvas pull "PHIL-123" -a "2.4 Discussion" --submissions ungraded --discussions
```

### 4) Edit rubrics locally

```bash
canvas pull "PHIL-123" --rubrics
canvas push -f "Philosophy/SP26-PHIL-123-codex-course/rubrics/Discussion-Rubric.yaml" --dry-run
canvas push -f "Philosophy/SP26-PHIL-123-codex-course/rubrics/Discussion-Rubric.yaml"
```

## Commands

| Command | Description |
|---|---|
| `canvas config` | Create `.canvas-config.yaml` in current folder |
| `canvas courses` | List your courses |
| `canvas modules COURSE` | List modules in a course |
| `canvas items COURSE MODULE` | List module items |
| `canvas rubrics COURSE` | List course rubrics |
| `canvas pull COURSE [options]` | Pull content from Canvas |
| `canvas push [options]` | Push local changes back |
| `canvas attach-rubric COURSE ...` | Attach rubric to assignments |
| `canvas status` | Count local synced files |

## Configuration

`canvas config` writes `.canvas-config.yaml`.

Example:

```yaml
canvas_url: https://your-school.instructure.com
api_token: YOUR_TOKEN

course_folders:
  ENGL: English
  PHIL: Philosophy
  HIST: History

default_folder: courses
```

Folder routing behavior:

- Matching prefixes route to configured folders (for example `ENGL -> English`)
- Non-matching courses go to `default_folder`
- Standard Canvas names like `2026SP-ENGL-101-001` become `SP26-ENGL-101-codex-course`

## Safety Rules

- Run `--dry-run` before any real `push`
- Keep `canvas_id` in frontmatter; it links files to Canvas objects
- Confirm changes before publishing to live courses
- Prefer small, targeted pushes (`--file`) over broad pushes when possible

## File Formats

### Pages/Assignments/Discussions (`.md`)

```markdown
---
canvas_id: 316993
title: 1.5 Assignment
due_at: '2026-01-26T06:59:59Z'
points_possible: 20.0
submission_types: [online_text_entry, online_upload]
published: true
---

Assignment content in markdown...
```

### Rubrics (`.yaml`)

```yaml
canvas_id: 19841  # set null to create a new rubric
title: Essay Rubric
points_possible: 20.0
criteria:
- id: _criterion1
  title: Thesis
  description: Clear, arguable thesis statement
  points: 10.0
```

## Codex Skill Usage

When this repo is available at `~/.codex/skills/canvas`, Codex can:

- Discover and run `canvas` commands
- Pull files before editing
- Suggest safe publish flow (`--dry-run` then push)
- Preserve Canvas-linked frontmatter fields

## Development

```bash
python -m unittest discover -s tests -v
```

## License

MIT
