"""Canvas CLI - Command line interface for Canvas LMS."""

import re
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from .api import CanvasAPI
from .config import load_config, get_courses_dir, get_course_folder, save_config
from .converters import html_to_markdown, markdown_to_html


def get_api() -> CanvasAPI:
    """Get configured Canvas API instance."""
    config = load_config()
    return CanvasAPI(config["canvas_url"], config["api_token"])


def slugify(text: str) -> str:
    """Convert text to a safe filename."""
    # Remove or replace problematic characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    return text[:100]  # Limit length


def matches_name(search: str, target: str) -> bool:
    """Check if search term matches target with word boundary awareness.

    '1.5' matches '1.5 Assignment' but not '11.5 Assignment'
    'Module 1' matches 'Module 1 - Intro' but not 'Module 10'
    """
    search_lower = search.lower().strip()
    target_lower = target.lower()

    # Escape special regex characters in search term, but keep it as literal
    escaped = re.escape(search_lower)

    # Match at word boundaries (start/end of string, spaces, or before/after non-alphanumeric)
    # Use word boundary \b for letters/numbers, but also handle cases like "1.5"
    pattern = r'(?:^|(?<=\s)|(?<=[^\w.]))' + escaped + r'(?:$|(?=\s)|(?=[^\w.]))'

    if re.search(pattern, target_lower):
        return True

    # Also try simpler word boundary match
    pattern_simple = r'\b' + escaped + r'\b'
    if re.search(pattern_simple, target_lower):
        return True

    return False


def find_course_by_name(api: CanvasAPI, name: str) -> Optional[dict]:
    """Find a course by partial name match. Prompts if multiple matches found."""
    name_lower = name.lower()
    matches = []
    for course in api.get_courses():
        if name_lower in course.get("name", "").lower() or name_lower in course.get("course_code", "").lower():
            matches.append(course)

    if not matches:
        return None

    if len(matches) == 1:
        return matches[0]

    # Multiple matches - prompt user to choose
    click.echo(f"\nMultiple courses match '{name}'.")
    click.echo("Use a more specific term or numeric course ID to avoid selecting the wrong course.\n")
    for i, course in enumerate(matches, 1):
        click.echo(
            f"  {i}. [{course['id']}] "
            f"{course.get('course_code', 'N/A')}  {course.get('name', 'Unknown')}"
        )
    click.echo()

    while True:
        choice = click.prompt("Enter number to select course", type=int)
        if 1 <= choice <= len(matches):
            return matches[choice - 1]
        click.echo(f"Please enter a number between 1 and {len(matches)}")


def find_module_by_name(api: CanvasAPI, course_id: int, name: str) -> Optional[dict]:
    """Find a module by partial name match."""
    name_lower = name.lower()
    for module in api.get_modules(course_id):
        if name_lower in module.get("name", "").lower():
            return module
    return None


@click.group()
@click.version_option()
def cli():
    """Canvas CLI - Pull and push content from Canvas LMS."""
    pass


# ==================== Config ====================

@cli.command()
@click.option("--url", prompt="Canvas URL", help="Canvas instance URL (e.g., https://school.instructure.com)")
@click.option("--token", prompt="API Token", hide_input=True, help="Canvas API token")
def config(url: str, token: str):
    """Configure Canvas CLI with your credentials."""
    config_data = {
        "canvas_url": url.rstrip("/"),
        "api_token": token,
        "default_folder": "courses"
    }

    config_path = Path.cwd() / ".canvas-config.yaml"
    save_config(config_data, config_path)
    click.echo(f"Configuration saved to {config_path}")


# ==================== List Commands ====================

@cli.command()
def courses():
    """List all available courses."""
    api = get_api()
    for course in api.get_courses():
        click.echo(f"{course['id']:>6}  {course.get('course_code', 'N/A'):<40}  {course.get('name', 'Unnamed')}")


@cli.command()
@click.argument("course")
def modules(course: str):
    """List all modules in a course."""
    api = get_api()

    # Try to find course by ID or name
    try:
        course_id = int(course)
    except ValueError:
        found = find_course_by_name(api, course)
        if not found:
            click.echo(f"Course not found: {course}", err=True)
            sys.exit(1)
        course_id = found["id"]
        click.echo(f"Found course: {found['name']} (ID: {course_id})\n")

    for module in api.get_modules(course_id):
        status = "published" if module.get("published") else "unpublished"
        click.echo(f"{module['id']:>8}  [{status:<11}]  {module.get('name', 'Unnamed')}")


@cli.command()
@click.argument("course")
@click.argument("module")
def items(course: str, module: str):
    """List all items in a module."""
    api = get_api()

    # Find course
    try:
        course_id = int(course)
    except ValueError:
        found = find_course_by_name(api, course)
        if not found:
            click.echo(f"Course not found: {course}", err=True)
            sys.exit(1)
        course_id = found["id"]

    # Find module
    try:
        module_id = int(module)
    except ValueError:
        found = find_module_by_name(api, course_id, module)
        if not found:
            click.echo(f"Module not found: {module}", err=True)
            sys.exit(1)
        module_id = found["id"]
        click.echo(f"Found module: {found['name']} (ID: {module_id})\n")

    for item in api.get_module_items(course_id, module_id):
        item_type = item.get("type", "Unknown")
        click.echo(f"{item.get('content_id', 'N/A'):>8}  [{item_type:<12}]  {item.get('title', 'Unnamed')}")


@cli.command()
@click.argument("course")
def rubrics(course: str):
    """List all rubrics in a course."""
    api = get_api()

    try:
        course_id = int(course)
    except ValueError:
        found = find_course_by_name(api, course)
        if not found:
            click.echo(f"Course not found: {course}", err=True)
            sys.exit(1)
        course_id = found["id"]

    for rubric in api.get_rubrics(course_id):
        click.echo(f"{rubric['id']:>8}  {rubric.get('points_possible', 0):>6} pts  {rubric.get('title', 'Unnamed')}")


@cli.command("attach-rubric")
@click.argument("course")
@click.option("-r", "--rubric", "rubric_name", required=True, help="Rubric name or ID")
@click.option("-a", "--assignment", "assignment_names", multiple=True, required=True,
              help="Assignment name(s) to attach rubric to (can specify multiple)")
@click.option("--no-grading", is_flag=True, help="Don't use rubric for grading (view only)")
@click.option("--dry-run", is_flag=True, help="Preview changes without making them")
def attach_rubric(course: str, rubric_name: str, assignment_names: tuple, no_grading: bool, dry_run: bool):
    """Attach a rubric to one or more assignments.

    Examples:
        canvas attach-rubric 8586 -r "Weekly Discussion" -a "1.4" -a "2.4" -a "3.4"
        canvas attach-rubric PHIL-123 -r 19841 -a "1.4 Moral Judgments Discussion"
    """
    api = get_api()

    if dry_run:
        click.echo("[DRY RUN] No changes will be made.\n")

    # Resolve course
    try:
        course_id = int(course)
    except ValueError:
        found = find_course_by_name(api, course)
        if not found:
            click.echo(f"Course not found: {course}", err=True)
            sys.exit(1)
        course_id = found["id"]
        click.echo(f"Course: {found.get('name', course)}")

    # Resolve rubric
    try:
        rubric_id = int(rubric_name)
        rubric_title = rubric_name
    except ValueError:
        # Search by name
        rubric_id = None
        for rubric in api.get_rubrics(course_id):
            if rubric_name.lower() in rubric.get("title", "").lower():
                rubric_id = rubric["id"]
                rubric_title = rubric.get("title", rubric_name)
                break
        if not rubric_id:
            click.echo(f"Rubric not found: {rubric_name}", err=True)
            sys.exit(1)

    click.echo(f"Rubric: {rubric_title} (ID: {rubric_id})")
    click.echo(f"Use for grading: {not no_grading}\n")

    # Get all assignments for matching
    assignments = list(api.get_assignments(course_id))

    # Match and attach to each assignment
    attached_count = 0
    for search_name in assignment_names:
        # Find matching assignment
        matched = None
        for assignment in assignments:
            if matches_name(search_name, assignment.get("name", "")):
                matched = assignment
                break

        if not matched:
            click.echo(f"  Assignment not found: {search_name}", err=True)
            continue

        assignment_id = matched["id"]
        assignment_title = matched.get("name", search_name)

        if dry_run:
            click.echo(f"  Would attach to: {assignment_title}")
        else:
            try:
                api.attach_rubric_to_assignment(course_id, rubric_id, assignment_id,
                                                 use_for_grading=not no_grading)
                click.echo(f"  Attached to: {assignment_title}")
                attached_count += 1
            except Exception as e:
                click.echo(f"  Error attaching to {assignment_title}: {e}", err=True)

    if dry_run:
        click.echo(f"\n[DRY RUN] Would attach rubric to {len(assignment_names)} assignment(s)")
    else:
        click.echo(f"\nAttached rubric to {attached_count} assignment(s)")


# ==================== Pull Commands ====================

def save_page(course_dir: Path, page: dict, subdir: str = "pages") -> Path:
    """Save a page as markdown."""
    pages_dir = course_dir / subdir
    pages_dir.mkdir(parents=True, exist_ok=True)

    filename = slugify(page.get("title", page["url"])) + ".md"
    filepath = pages_dir / filename

    # Convert HTML to markdown
    body_html = page.get("body", "")
    body_md = html_to_markdown(body_html)

    # Create frontmatter
    frontmatter = {
        "canvas_id": page.get("page_id"),
        "canvas_url": page.get("url"),
        "title": page.get("title"),
        "published": page.get("published", False),
    }

    content = f"""---
{yaml.dump(frontmatter, default_flow_style=False).strip()}
---

{body_md}
"""

    filepath.write_text(content)
    return filepath


def save_assignment(course_dir: Path, assignment: dict, subdir: str = "assignments") -> Path:
    """Save an assignment as markdown."""
    assignments_dir = course_dir / subdir
    assignments_dir.mkdir(parents=True, exist_ok=True)

    filename = slugify(assignment.get("name", str(assignment["id"]))) + ".md"
    filepath = assignments_dir / filename

    # Convert HTML description to markdown
    desc_html = assignment.get("description", "") or ""
    desc_md = html_to_markdown(desc_html)

    # Create frontmatter
    frontmatter = {
        "canvas_id": assignment.get("id"),
        "title": assignment.get("name"),
        "due_at": assignment.get("due_at"),
        "points_possible": assignment.get("points_possible"),
        "submission_types": assignment.get("submission_types"),
        "published": assignment.get("published", False),
        "rubric_id": assignment.get("rubric_settings", {}).get("id") if assignment.get("rubric_settings") else None,
    }
    # Remove None values
    frontmatter = {k: v for k, v in frontmatter.items() if v is not None}

    content = f"""---
{yaml.dump(frontmatter, default_flow_style=False).strip()}
---

{desc_md}
"""

    filepath.write_text(content)
    return filepath


def save_rubric(course_dir: Path, rubric: dict) -> Path:
    """Save a rubric as YAML."""
    rubrics_dir = course_dir / "rubrics"
    rubrics_dir.mkdir(parents=True, exist_ok=True)

    filename = slugify(rubric.get("title", str(rubric["id"]))) + ".yaml"
    filepath = rubrics_dir / filename

    # Extract and simplify rubric data
    rubric_data = {
        "canvas_id": rubric.get("id"),
        "title": rubric.get("title"),
        "points_possible": rubric.get("points_possible"),
        "criteria": []
    }

    for criterion in rubric.get("data", []):
        crit_data = {
            "id": criterion.get("id"),
            "title": criterion.get("title") or criterion.get("description"),
            "description": criterion.get("long_description"),
            "points": criterion.get("points"),
            "ratings": []
        }
        for rating in criterion.get("ratings", []):
            crit_data["ratings"].append({
                "id": rating.get("id"),
                "description": rating.get("description"),
                "long_description": rating.get("long_description"),
                "points": rating.get("points")
            })
        rubric_data["criteria"].append(crit_data)

    filepath.write_text(yaml.dump(rubric_data, default_flow_style=False, allow_unicode=True))
    return filepath


def convert_rubric_to_canvas_format(rubric_data: dict) -> dict:
    """Convert local rubric YAML format to Canvas API format.

    Canvas expects criteria as indexed dict, not array:
    {"0": {...}, "1": {...}} instead of [{...}, {...}]
    """
    canvas_rubric = {
        "title": rubric_data.get("title"),
        "points_possible": rubric_data.get("points_possible"),
    }

    criteria = {}
    for i, criterion in enumerate(rubric_data.get("criteria", [])):
        ratings = {}
        for j, rating in enumerate(criterion.get("ratings", [])):
            ratings[str(j)] = {
                "description": rating.get("description", ""),
                "long_description": rating.get("long_description", ""),
                "points": rating.get("points", 0),
            }
            # Include ID if it exists (for updating existing ratings)
            if rating.get("id"):
                ratings[str(j)]["id"] = rating["id"]

        criteria[str(i)] = {
            "description": criterion.get("title", ""),
            "long_description": criterion.get("description", ""),
            "points": criterion.get("points", 0),
            "ratings": ratings,
        }
        # Include ID if it exists (for updating existing criteria)
        if criterion.get("id"):
            criteria[str(i)]["id"] = criterion["id"]

    canvas_rubric["criteria"] = criteria
    return canvas_rubric


def push_rubric_file(api: CanvasAPI, filepath: Path, dry_run: bool = False) -> bool:
    """Push a rubric YAML file to Canvas. Returns True if successful.

    If canvas_id is null/None, creates a new rubric and updates the local file
    with the returned canvas_id. Otherwise, updates the existing rubric.
    """
    try:
        rubric_data = yaml.safe_load(filepath.read_text())
    except Exception as e:
        click.echo(f"  Error reading {filepath.name}: {e}", err=True)
        return False

    rubric_id = rubric_data.get("canvas_id")
    is_new = rubric_id is None

    try:
        course_meta = find_course_meta(filepath)
        course_id = course_meta["canvas_id"]
    except FileNotFoundError as e:
        click.echo(f"  Error: {e}", err=True)
        return False

    canvas_format = convert_rubric_to_canvas_format(rubric_data)

    action = "Creating" if is_new else "Updating"
    click.echo(f"  {action} rubric: {rubric_data.get('title', filepath.name)}")
    click.echo(f"    Criteria: {len(rubric_data.get('criteria', []))}")

    if not dry_run:
        if is_new:
            # Create new rubric
            result = api.create_rubric(course_id, **canvas_format)
            new_id = result.get("rubric", {}).get("id") or result.get("id")
            if new_id:
                # Update local file with the new canvas_id
                rubric_data["canvas_id"] = new_id
                filepath.write_text(yaml.dump(rubric_data, default_flow_style=False, allow_unicode=True))
                click.echo(f"    Created with ID: {new_id}")
            else:
                click.echo(f"    Warning: Could not get ID from response", err=True)
        else:
            # Update existing rubric
            api.update_rubric(course_id, rubric_id, **canvas_format)

    return True


def save_discussion_entries(course_dir: Path, topic_name: str, topic_id: int, api: CanvasAPI, course_id: int) -> Path:
    """Save discussion entries (posts and replies) as markdown."""
    from datetime import datetime

    discussions_dir = course_dir / "discussions"
    discussions_dir.mkdir(parents=True, exist_ok=True)

    filename = slugify(topic_name) + "-entries.md"
    filepath = discussions_dir / filename

    # Get full discussion view
    data = api.get_discussion_entries(course_id, topic_id)

    # Build participant lookup
    participants = {p['id']: p.get('display_name', f"User {p['id']}") for p in data.get('participants', [])}

    output = []
    output.append(f"# {topic_name} - Student Posts\n")
    output.append(f"*Pulled: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    def format_entry(entry, indent=0):
        """Format a discussion entry with replies."""
        lines = []
        prefix = "  " * indent
        heading = "##" if indent == 0 else "###"

        user_name = participants.get(entry.get('user_id'), 'Unknown')
        posted = entry.get('created_at', 'Unknown date')
        if posted != 'Unknown date':
            posted = posted[:10]

        lines.append(f"{prefix}{heading} {user_name}")
        lines.append(f"{prefix}*Posted: {posted}*\n")

        message = entry.get('message', '(No content)')
        # Clean up HTML
        message = re.sub(r'<p>', '', message)
        message = re.sub(r'</p>', '\n', message)
        message = re.sub(r'<br\s*/?>', '\n', message)
        message = re.sub(r'<[^>]+>', '', message)
        message = message.strip()

        # Indent message content for nested replies
        if indent > 0:
            message = '\n'.join(prefix + line for line in message.split('\n'))
        lines.append(f"{message}\n")

        # Handle replies
        replies = entry.get('replies', [])
        if replies:
            lines.append(f"{prefix}**Replies:**\n")
            for reply in replies:
                lines.extend(format_entry(reply, indent + 1))

        return lines

    entries = data.get('view', [])
    for entry in entries:
        output.extend(format_entry(entry))
        output.append("---\n")

    filepath.write_text('\n'.join(output))
    return filepath


def save_submission(course_dir: Path, assignment_name: str, submission: dict,
                    user_info: dict, api: "CanvasAPI" = None) -> Optional[Path]:
    """Save a submission as markdown and download any attachments."""
    import requests

    submissions_dir = course_dir / "submissions" / slugify(assignment_name)
    submissions_dir.mkdir(parents=True, exist_ok=True)

    # Get user name
    user_name = user_info.get("name", f"user-{submission.get('user_id')}")
    user_slug = slugify(user_name)
    filename = user_slug + ".md"
    filepath = submissions_dir / filename

    # Get submission body
    body = submission.get("body", "") or ""
    if submission.get("submission_type") == "online_url":
        body = f"URL: {submission.get('url', 'N/A')}\n\n{body}"

    body_md = html_to_markdown(body) if body else "(No submission content)"

    # Download attachments
    attachments = submission.get("attachments", [])
    attachment_files = []
    for i, attachment in enumerate(attachments):
        url = attachment.get("url")
        original_filename = attachment.get("filename", f"attachment-{i+1}")
        # Get file extension
        ext = Path(original_filename).suffix or ""
        # Create filename: StudentName.ext or StudentName-2.ext for multiple
        if len(attachments) == 1:
            att_filename = f"{user_slug}{ext}"
        else:
            att_filename = f"{user_slug}-{i+1}{ext}"

        att_filepath = submissions_dir / att_filename

        if url:
            try:
                if api:
                    resp = api.session.get(url, timeout=30)
                else:
                    resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                att_filepath.write_bytes(resp.content)
                attachment_files.append(att_filename)
            except Exception as e:
                click.echo(f"      Warning: Failed to download {original_filename}: {e}")

    # Get comments
    comments_md = ""
    for comment in submission.get("submission_comments", []):
        author = comment.get("author_name", "Unknown")
        date = comment.get("created_at", "")[:10] if comment.get("created_at") else ""
        text = comment.get("comment", "")
        comments_md += f"\n### {author} ({date})\n{text}\n"

    # Create frontmatter
    frontmatter = {
        "student_id": submission.get("user_id"),
        "student_name": user_name,
        "submitted_at": submission.get("submitted_at"),
        "grade": submission.get("grade"),
        "score": submission.get("score"),
        "workflow_state": submission.get("workflow_state"),
        "late": submission.get("late", False),
        "attempt": submission.get("attempt"),
    }
    if attachment_files:
        frontmatter["attachments"] = attachment_files
    frontmatter = {k: v for k, v in frontmatter.items() if v is not None}

    # Build attachments section for markdown
    attachments_md = ""
    if attachment_files:
        attachments_md = "\n## Attachments\n"
        for att_file in attachment_files:
            attachments_md += f"- [{att_file}]({att_file})\n"

    content = f"""---
{yaml.dump(frontmatter, default_flow_style=False).strip()}
---

# Submission

{body_md}
{attachments_md}
## Comments
{comments_md if comments_md else "(No comments)"}
"""

    filepath.write_text(content)
    return filepath


@cli.command()
@click.argument("course")
@click.option("-m", "--module", "module_name", help="Pull specific module by name")
@click.option("-p", "--page", "page_name", help="Pull specific page by name")
@click.option("-a", "--assignment", "assignment_name", help="Pull specific assignment by name")
@click.option("-d", "--discussion", "discussion_name", help="Pull specific discussion with all posts/replies")
@click.option("--rubrics/--no-rubrics", default=False, help="Include rubrics")
@click.option("--submissions", type=click.Choice(["all", "ungraded", "none"]), default="none",
              help="Include submissions")
@click.option("--discussions/--no-discussions", "include_discussions", default=False,
              help="Include discussion posts/replies when pulling assignments")
def pull(course: str, module_name: Optional[str], page_name: Optional[str],
         assignment_name: Optional[str], discussion_name: Optional[str],
         rubrics: bool, submissions: str, include_discussions: bool):
    """Pull content from Canvas to local files."""
    api = get_api()

    # Find course
    try:
        course_id = int(course)
        course_data = api.get_course(course_id)
    except ValueError:
        course_data = find_course_by_name(api, course)
        if not course_data:
            click.echo(f"Course not found: {course}", err=True)
            sys.exit(1)
        course_id = course_data["id"]

    course_name = course_data.get("name", f"course-{course_id}")
    course_code = course_data.get("course_code", "")
    click.echo(f"Pulling from: {course_name}")

    # Get course directory based on course code mapping
    course_dir = get_course_folder(course_code, course_name)
    course_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"  -> {course_dir}")

    # Save course metadata
    course_meta = {
        "canvas_id": course_id,
        "name": course_name,
        "code": course_data.get("course_code"),
    }
    (course_dir / "_course.yaml").write_text(yaml.dump(course_meta, default_flow_style=False))

    pulled_count = 0

    # Pull specific page
    if page_name:
        for page in api.get_pages(course_id):
            if matches_name(page_name, page.get("title", "")):
                full_page = api.get_page(course_id, page["url"])
                filepath = save_page(course_dir, full_page)
                click.echo(f"  Pulled page: {filepath.name}")
                pulled_count += 1
        if pulled_count == 0:
            click.echo(f"No pages found matching: {page_name}", err=True)
        return

    # Pull specific discussion by name
    if discussion_name:
        for topic in api.get_discussion_topics(course_id):
            if matches_name(discussion_name, topic.get("title", "")):
                # Save the discussion topic itself
                disc_data = {
                    "page_id": topic["id"],
                    "url": f"discussion-{topic['id']}",
                    "title": topic.get("title", "Discussion"),
                    "body": topic.get("message", ""),
                    "published": topic.get("published", False),
                }
                filepath = save_page(course_dir, disc_data, subdir="discussions")
                click.echo(f"  Pulled discussion: {filepath.name}")

                # Pull discussion entries (posts and replies)
                click.echo(f"  Pulling discussion posts...")
                entries_path = save_discussion_entries(
                    course_dir, topic["title"], topic["id"], api, course_id
                )
                entry_count = len(api.get_discussion_entries(course_id, topic["id"]).get("view", []))
                click.echo(f"    {entry_count} posts saved to: {entries_path.name}")
                pulled_count += 1

        if pulled_count == 0:
            click.echo(f"No discussions found matching: {discussion_name}", err=True)
        return

    # Pull specific assignment
    if assignment_name:
        for assignment in api.get_assignments(course_id):
            if matches_name(assignment_name, assignment.get("name", "")):
                filepath = save_assignment(course_dir, assignment)
                click.echo(f"  Pulled assignment: {filepath.name}")
                pulled_count += 1

                # Check if this is a discussion assignment
                is_discussion = "discussion_topic" in assignment.get("submission_types", [])

                # Pull discussion entries if requested and it's a discussion
                if include_discussions and is_discussion:
                    # Find the discussion topic for this assignment
                    for topic in api.get_discussion_topics(course_id):
                        if topic.get("assignment_id") == assignment["id"]:
                            click.echo(f"  Pulling discussion posts...")
                            entries_path = save_discussion_entries(
                                course_dir, assignment["name"], topic["id"], api, course_id
                            )
                            entry_count = len(api.get_discussion_entries(course_id, topic["id"]).get("view", []))
                            click.echo(f"    {entry_count} posts saved to: {entries_path.name}")
                            break

                # Pull submissions for this assignment if requested
                if submissions != "none":
                    click.echo(f"  Pulling submissions...")
                    for sub in api.get_submissions(course_id, assignment["id"]):
                        if submissions == "ungraded" and sub.get("grade") is not None:
                            continue
                        if sub.get("workflow_state") == "unsubmitted":
                            continue
                        user_info = sub.get("user", {})
                        save_submission(course_dir, assignment["name"], sub, user_info, api=api)
                        click.echo(f"    Submission: {user_info.get('name', 'Unknown')}")

        if pulled_count == 0:
            click.echo(f"No assignments found matching: {assignment_name}", err=True)
        return

    # Pull specific module
    if module_name:
        module_data = find_module_by_name(api, course_id, module_name)
        if not module_data:
            click.echo(f"Module not found: {module_name}", err=True)
            sys.exit(1)

        module_dir = course_dir / slugify(module_data["name"])
        module_dir.mkdir(parents=True, exist_ok=True)

        # Save module metadata
        module_meta = {
            "canvas_id": module_data["id"],
            "name": module_data["name"],
            "position": module_data.get("position"),
            "unlock_at": module_data.get("unlock_at"),
            "require_sequential_progress": module_data.get("require_sequential_progress"),
            "published": module_data.get("published"),
        }
        (module_dir / "_module.yaml").write_text(yaml.dump(module_meta, default_flow_style=False))

        click.echo(f"  Pulling module: {module_data['name']}")

        for item in api.get_module_items(course_id, module_data["id"]):
            item_type = item.get("type")

            if item_type == "Page":
                page = api.get_page(course_id, item["page_url"])
                filepath = save_page(course_dir, page, subdir=module_dir.name)
                click.echo(f"    Page: {filepath.name}")
                pulled_count += 1

            elif item_type == "Assignment":
                assignment = api.get_assignment(course_id, item["content_id"])
                filepath = save_assignment(course_dir, assignment, subdir=module_dir.name)
                click.echo(f"    Assignment: {filepath.name}")
                pulled_count += 1

            elif item_type == "Discussion":
                topic = api.get_discussion_topic(course_id, item["content_id"])
                # Save discussion as a page-like markdown
                disc_data = {
                    "page_id": topic["id"],
                    "url": f"discussion-{topic['id']}",
                    "title": topic.get("title", "Discussion"),
                    "body": topic.get("message", ""),
                    "published": topic.get("published", False),
                }
                filepath = save_page(course_dir, disc_data, subdir=module_dir.name)
                click.echo(f"    Discussion: {filepath.name}")
                pulled_count += 1

        click.echo(f"\nPulled {pulled_count} items from module.")
        return

    # Pull entire course
    click.echo("  Pulling all pages...")
    for page in api.get_pages(course_id):
        full_page = api.get_page(course_id, page["url"])
        save_page(course_dir, full_page)
        pulled_count += 1
    click.echo(f"    {pulled_count} pages")

    assignment_count = 0
    click.echo("  Pulling all assignments...")
    for assignment in api.get_assignments(course_id):
        save_assignment(course_dir, assignment)
        assignment_count += 1
    click.echo(f"    {assignment_count} assignments")
    pulled_count += assignment_count

    if rubrics:
        rubric_count = 0
        click.echo("  Pulling rubrics...")
        for rubric in api.get_rubrics(course_id):
            save_rubric(course_dir, rubric)
            rubric_count += 1
        click.echo(f"    {rubric_count} rubrics")
        pulled_count += rubric_count

    click.echo(f"\nTotal: {pulled_count} items pulled to {course_dir}")


# ==================== Push Commands ====================

def parse_markdown_file(filepath: Path) -> tuple[dict, str]:
    """Parse a markdown file with YAML frontmatter."""
    content = filepath.read_text()

    # Extract frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            if not isinstance(frontmatter, dict):
                frontmatter = {}
            body = parts[2].strip()
            return frontmatter, body

    return {}, content


def find_course_meta(filepath: Path) -> dict:
    """Find _course.yaml from a content file path."""
    # Try parent.parent first (for files in subdirectories)
    course_meta_path = filepath.parent.parent / "_course.yaml"
    if not course_meta_path.exists():
        # Try parent (for files directly in course folder)
        course_meta_path = filepath.parent / "_course.yaml"
    if not course_meta_path.exists():
        # Try going up further (for deeply nested files)
        for parent in filepath.parents:
            candidate = parent / "_course.yaml"
            if candidate.exists():
                course_meta_path = candidate
                break

    if not course_meta_path.exists():
        raise FileNotFoundError(
            f"Cannot find _course.yaml for {filepath}. Pull the course first to create local metadata."
        )

    return yaml.safe_load(course_meta_path.read_text())


def push_file(api: CanvasAPI, filepath: Path, dry_run: bool = False) -> bool:
    """Push a single file to Canvas. Returns True if successful."""
    frontmatter, body = parse_markdown_file(filepath)

    if "canvas_id" not in frontmatter:
        click.echo(f"  Skipping {filepath.name}: no canvas_id in frontmatter", err=True)
        return False

    try:
        course_meta = find_course_meta(filepath)
        course_id = course_meta["canvas_id"]
    except FileNotFoundError as e:
        click.echo(f"  Error: {e}", err=True)
        return False

    # Convert markdown back to HTML
    body_html = markdown_to_html(body)

    # Determine if it's a page, discussion, or assignment based on frontmatter
    submission_types = frontmatter.get("submission_types", [])
    is_discussion = "discussion_topic" in submission_types

    if "canvas_url" in frontmatter:
        # It's a page
        click.echo(f"  Page: {frontmatter.get('title', filepath.name)}")
        if not dry_run:
            api.update_page(course_id, frontmatter["canvas_url"], body=body_html)
    elif is_discussion:
        # It's a discussion topic - need to find topic_id from assignment_id
        click.echo(f"  Discussion: {frontmatter.get('title', filepath.name)}")

        # Look up the discussion topic ID from assignment ID
        assignment_id = frontmatter["canvas_id"]
        topic_id = None

        # Check if topic_id is already in frontmatter
        if "discussion_topic_id" in frontmatter:
            topic_id = frontmatter["discussion_topic_id"]
        else:
            # Find the topic by matching assignment_id
            for topic in api.get_discussion_topics(course_id):
                if topic.get("assignment_id") == assignment_id:
                    topic_id = topic["id"]
                    break

        if not topic_id:
            click.echo(f"  Error: Could not find discussion topic for assignment {assignment_id}", err=True)
            return False

        update_data = {"message": body_html}
        if "title" in frontmatter:
            update_data["title"] = frontmatter["title"]
        if not dry_run:
            api.update_discussion_topic(course_id, topic_id, **update_data)
    elif "submission_types" in frontmatter or "points_possible" in frontmatter:
        # It's an assignment
        click.echo(f"  Assignment: {frontmatter.get('title', filepath.name)}")
        update_data = {"description": body_html}
        if "due_at" in frontmatter:
            update_data["due_at"] = frontmatter["due_at"]
        if "points_possible" in frontmatter:
            update_data["points_possible"] = frontmatter["points_possible"]
        if not dry_run:
            api.update_assignment(course_id, frontmatter["canvas_id"], **update_data)
    else:
        # Assume it's a page if it has canvas_url, otherwise try as generic content
        click.echo(f"  Unknown type: {filepath.name} - skipping", err=True)
        return False

    return True


@cli.command()
@click.option("-m", "--module", "module_name", help="Push specific module by name")
@click.option("-f", "--file", "file_path", type=click.Path(exists=True), help="Push specific file (auto-detects type)")
@click.option("--dry-run", is_flag=True, help="Preview changes without pushing")
def push(module_name: Optional[str], file_path: Optional[str], dry_run: bool):
    """Push local changes to Canvas."""
    api = get_api()
    courses_dir = get_courses_dir()

    if dry_run:
        click.echo("[DRY RUN] No changes will be made.\n")

    # Push specific file
    if file_path:
        filepath = Path(file_path)
        click.echo(f"Pushing: {filepath.name}")

        # Detect rubric files (YAML files in rubrics directory)
        if filepath.suffix == ".yaml" and "rubrics" in filepath.parts:
            success = push_rubric_file(api, filepath, dry_run)
        else:
            success = push_file(api, filepath, dry_run)

        if success:
            click.echo("Done!" if not dry_run else "[DRY RUN] Would push above.")
        return

    # Push module
    if module_name:
        # Find the module directory
        for course_path in courses_dir.iterdir():
            if not course_path.is_dir():
                continue

            for item_path in course_path.iterdir():
                if item_path.is_dir() and module_name.lower() in item_path.name.lower():
                    click.echo(f"Pushing module: {item_path.name}")

                    # Push all markdown files in the module
                    for md_file in item_path.glob("*.md"):
                        push_file(api, md_file, dry_run)

                    click.echo("\nDone!" if not dry_run else "\n[DRY RUN] Would push above items.")
                    return

        click.echo(f"Module directory not found: {module_name}", err=True)
        sys.exit(1)

    click.echo("Please specify what to push: --file or --module")
    sys.exit(1)


# ==================== Status Command ====================

@cli.command()
def status():
    """Show sync status of local files."""
    courses_dir = get_courses_dir()

    if not courses_dir.exists():
        click.echo("No courses directory found. Run 'canvas pull' first.")
        return

    for course_path in courses_dir.iterdir():
        if not course_path.is_dir():
            continue

        course_meta_path = course_path / "_course.yaml"
        if course_meta_path.exists():
            meta = yaml.safe_load(course_meta_path.read_text())
            click.echo(f"\n{meta.get('name', course_path.name)}")
            click.echo("-" * 40)

        # Count files
        pages = list(course_path.glob("**/*.md"))
        rubrics = list(course_path.glob("rubrics/*.yaml"))
        submissions = list(course_path.glob("submissions/**/*.md"))

        click.echo(f"  Pages/Assignments: {len(pages)}")
        click.echo(f"  Rubrics: {len(rubrics)}")
        click.echo(f"  Submissions: {len(submissions)}")


def main():
    cli()


if __name__ == "__main__":
    main()
