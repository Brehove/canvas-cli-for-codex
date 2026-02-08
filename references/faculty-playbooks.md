# Faculty Playbooks

## Update an assignment prompt

1. Pull assignment:
   `canvas pull "ENGL-101" -a "Essay 1"`
2. Ask Codex to revise clarity, rubric alignment, and student-facing tone.
3. Preview push:
   `canvas push -f ".../assignments/Essay-1.md" --dry-run`
4. Push when confirmed.

## Shift due dates for one activity

1. Pull assignment.
2. Update `due_at` in frontmatter.
3. Preview and push file.

## Review ungraded discussion submissions

1. Pull with submissions + discussions:
   `canvas pull "COURSE" -a "Discussion Name" --submissions ungraded --discussions`
2. Ask Codex to summarize themes, flag missing requirements, and draft feedback snippets.

## Update a rubric and attach it

1. Pull rubrics: `canvas pull "COURSE" --rubrics`
2. Edit rubric YAML criteria/ratings.
3. Preview + push rubric file.
4. Attach rubric:
   `canvas attach-rubric "COURSE" -r "Rubric Name" -a "Assignment Name" --dry-run`
   then rerun without `--dry-run`.

## Prompt templates for Codex

- "Pull my ENGL-101 syllabus page, rewrite it for plain language accessibility, and show a dry-run push command."
- "Update Assignment 2 instructions for transparency and add a clearer grading criteria section. Preserve points and due date."
- "Summarize ungraded discussion submissions and draft 3 reusable feedback comments aligned to the rubric."
