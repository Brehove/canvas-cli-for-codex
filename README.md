# Canvas CLI for Codex

This is a Codex skill package that lets faculty and staff use natural language to work with Canvas course content inside their local filesystem.
Instead of memorizing commands, you can ask Codex things like:

- `Use the canvas skill to pull my entire course.`
- `Evaluate everything for accessibility and give me an update plan.`
- `After I approve, apply updates and push all module changes.`

Codex then uses the Canvas CLI for pull/edit/push steps while keeping files local in your working folders.
The skill also preserves HTML tables during conversion so accessibility markup (captions, header scope, and table structure) is retained instead of being flattened by standard markdown table syntax.

Before using this skill, set up Codex first:
- Codex setup guide: https://developers.openai.com/codex/cli
- Codex overview: https://openai.com/codex/

## Using Claude Code Instead of Codex

You can use this same skill with Claude Code by installing it in `~/.claude/skills/canvas` and running the same `canvas` commands/workflows.

This package is intentionally optimized for Codex because many higher-ed institutions currently have enterprise agreements with OpenAI rather than Anthropic. If your institution uses Claude Code, the workflow still works with only the skill install path changed.

## What This Solves

- Pull pages, assignments, discussions, rubrics, and submissions from Canvas
- Edit content locally with full YAML frontmatter metadata
- Push only what you intend, with `--dry-run` previews first
- Use Codex to draft, revise, and QA course content before syncing

## Easiest Setup (Ask Codex To Do It)

This is the recommended path for faculty/staff who are new to terminal tools.

1. Open Terminal.
2. Start Codex CLI.
3. Paste this request to Codex:

```text
I am new to terminal workflows.
Please install and set up this Canvas skill from:
https://github.com/Brehove/canvas-cli-for-codex

Please handle any skill-path details for me automatically.
Then walk me through first-time setup step by step.
```

4. Follow Codex prompts. It may ask for approval before running install commands.
5. If Codex says new skills are not loaded yet, restart Codex once.

## Manual Setup (Optional)

Use this only if you want to run commands yourself.

```bash
# 1) Install the CLI package from the installed skill folder
pip install -e ~/.codex/skills/canvas

# 2) Create a working folder for your term
mkdir -p ~/canvas-work/spring-2026
cd ~/canvas-work/spring-2026

# 3) Configure Canvas access
canvas config
# Prompts for Canvas URL and API token

# 4) Verify access
canvas courses
```

## Find Your Canvas API Token

1. Log in to Canvas in your browser.
2. In the left menu, select `Account`, then `Settings`.
3. Find and select `+ New Access Token`.
4. Enter a purpose (example: `Codex Canvas CLI`) and optional expiration date.
5. Select create/generate token.
6. Copy the token immediately and paste it into `canvas config` when prompted.
   If needed, you can also paste it manually into `.canvas-config.yaml` as the `api_token` value.

Treat the token like a password. If it is exposed, revoke it in Canvas and create a new one.
If your Canvas account does not show token creation, contact your Canvas admin.

## Faculty Workflows (Codex + Canvas)

The skill package teaches Codex how to:

- run the right `canvas` commands for pull/push
- preserve required Canvas metadata (`canvas_id`)
- use a safe publish flow (`--dry-run` before real push)
- keep HTML tables intact so accessibility markup is not lost

That means you can use plain-language requests instead of memorizing commands.

### Start each session (first thing to do)

1. Open Terminal in the folder for the course you want to work on.
2. Start Codex in that folder.
3. If this is your first time in that folder, ask Codex:
   `Use the canvas skill to help me run canvas config in this folder.`
   Codex should prompt you to enter your Canvas URL and API token via `canvas config` (token entry is hidden).
   You can also add the token manually in `.canvas-config.yaml` under `api_token`.
4. For day-to-day work, start with:
   `Use the canvas skill to help me update content in [COURSE NAME].`

Why this matters:
- The CLI does not read config from the skill folder. It looks from your current folder upward through parent folders.
- You usually need only one shared config at a root folder (example: `~/canvas-work/.canvas-config.yaml`), then all course subfolders under that root can use it.
- Keeping each term/course in its own folder makes files easier to manage.

### Example prompts you can paste to Codex

1. Update one assignment:
   `Pull Essay 1 from ENGL-101, rewrite for clarity and student-friendly tone, keep points and due date the same, then show me a dry-run push command.`

2. Improve a module for accessibility:
   `Use the canvas skill to pull all modules in PHIL-123. Evaluate all pulled module content for accessibility issues (heading structure, descriptive link text, table headers/captions, list structure, and image alt text opportunities). Then give me a module-by-module update plan with recommended edits and risk notes. Wait for my approval before making changes. After I approve, apply the updates and show dry-run push commands for each updated module. After I confirm again, push the updated modules to Canvas.`

3. Make a table fully accessible:
   `Find the grading table in this pulled assignment, add a caption and proper column/row headers with scope attributes, preserve table structure, then show me the dry-run push command.`

4. Review ungraded discussions:
   `Pull ungraded submissions for 2.4 Discussion in PHIL-123 (including discussion posts), summarize common issues, and draft reusable feedback comments.`

5. Update and attach a rubric:
   `Pull rubrics for PHIL-123, revise the Discussion rubric for clearer performance levels, run a dry-run push, then attach it to assignment 2.4 after I confirm.`

If you prefer manual commands, see the command reference below.

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
