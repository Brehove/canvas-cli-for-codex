"""Canvas LMS API wrapper."""

import requests
from typing import Optional, Iterator, Any
from urllib.parse import urljoin


def _flatten_form_fields(prefix: str, value: Any) -> list[tuple[str, str]]:
    """Flatten nested Canvas parameters into Rails-style bracket fields."""
    fields: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            fields.extend(_flatten_form_fields(f"{prefix}[{key}]", item))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            fields.extend(_flatten_form_fields(f"{prefix}[{index}]", item))
    elif value is not None:
        if isinstance(value, bool):
            value = str(value).lower()
        fields.append((prefix, str(value)))
    return fields


class CanvasAPI:
    """Wrapper for Canvas LMS REST API."""

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request."""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def _get(self, endpoint: str, **kwargs) -> Any:
        """GET request returning JSON."""
        return self._request("GET", endpoint, **kwargs).json()

    def _put(self, endpoint: str, **kwargs) -> Any:
        """PUT request returning JSON."""
        return self._request("PUT", endpoint, **kwargs).json()

    def _post(self, endpoint: str, **kwargs) -> Any:
        """POST request returning JSON."""
        return self._request("POST", endpoint, **kwargs).json()

    def _delete(self, endpoint: str, **kwargs) -> Any:
        """DELETE request."""
        return self._request("DELETE", endpoint, **kwargs)

    def _paginate(self, endpoint: str, **kwargs) -> Iterator[Any]:
        """Iterate through paginated results."""
        params = kwargs.pop("params", {})
        params.setdefault("per_page", 100)

        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        while url:
            response = self.session.get(url, params=params, **kwargs)
            response.raise_for_status()

            for item in response.json():
                yield item

            # Get next page from Link header
            url = None
            params = {}  # Clear params for subsequent requests (they're in the URL)
            if "Link" in response.headers:
                links = response.headers["Link"].split(",")
                for link in links:
                    if 'rel="next"' in link:
                        url = link.split(";")[0].strip(" <>")
                        break

    # ==================== Courses ====================

    def get_courses(self) -> Iterator[dict]:
        """Get all courses for the current user."""
        return self._paginate("courses")

    def get_course(self, course_id: int) -> dict:
        """Get a specific course."""
        return self._get(f"courses/{course_id}")

    # ==================== Modules ====================

    def get_modules(self, course_id: int) -> Iterator[dict]:
        """Get all modules in a course."""
        return self._paginate(f"courses/{course_id}/modules")

    def get_module(self, course_id: int, module_id: int) -> dict:
        """Get a specific module."""
        return self._get(f"courses/{course_id}/modules/{module_id}")

    def get_module_items(self, course_id: int, module_id: int) -> Iterator[dict]:
        """Get all items in a module."""
        return self._paginate(f"courses/{course_id}/modules/{module_id}/items")

    def update_module(self, course_id: int, module_id: int, **kwargs) -> dict:
        """Update a module."""
        return self._put(f"courses/{course_id}/modules/{module_id}", json={"module": kwargs})

    # ==================== Pages ====================

    def get_pages(self, course_id: int) -> Iterator[dict]:
        """Get all pages in a course."""
        return self._paginate(f"courses/{course_id}/pages")

    def get_page(self, course_id: int, page_url: str) -> dict:
        """Get a specific page by URL slug."""
        return self._get(f"courses/{course_id}/pages/{page_url}")

    def update_page(self, course_id: int, page_url: str, **kwargs) -> dict:
        """Update a page."""
        return self._put(f"courses/{course_id}/pages/{page_url}", json={"wiki_page": kwargs})

    def create_page(self, course_id: int, **kwargs) -> dict:
        """Create a new page."""
        return self._post(f"courses/{course_id}/pages", json={"wiki_page": kwargs})

    # ==================== Assignments ====================

    def get_assignments(self, course_id: int) -> Iterator[dict]:
        """Get all assignments in a course."""
        return self._paginate(f"courses/{course_id}/assignments")

    def get_assignment(self, course_id: int, assignment_id: int) -> dict:
        """Get a specific assignment."""
        return self._get(f"courses/{course_id}/assignments/{assignment_id}")

    def update_assignment(self, course_id: int, assignment_id: int, **kwargs) -> dict:
        """Update an assignment."""
        return self._put(f"courses/{course_id}/assignments/{assignment_id}", json={"assignment": kwargs})

    # ==================== Rubrics ====================

    def get_rubrics(self, course_id: int) -> Iterator[dict]:
        """Get all rubrics in a course."""
        return self._paginate(f"courses/{course_id}/rubrics")

    def get_rubric(self, course_id: int, rubric_id: int) -> dict:
        """Get a specific rubric with full details."""
        return self._get(f"courses/{course_id}/rubrics/{rubric_id}", params={"include[]": "assessments"})

    def update_rubric(self, course_id: int, rubric_id: int,
                      rubric_association: Optional[dict] = None, **kwargs) -> dict:
        """Update a rubric."""
        fields = _flatten_form_fields("rubric", kwargs)
        if rubric_association:
            fields.extend(
                _flatten_form_fields("rubric_association", rubric_association)
            )
        return self._put(
            f"courses/{course_id}/rubrics/{rubric_id}",
            data=fields,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def create_rubric(self, course_id: int,
                      rubric_association: Optional[dict] = None, **kwargs) -> dict:
        """Create a new rubric."""
        fields = _flatten_form_fields("rubric", kwargs)
        if rubric_association:
            fields.extend(
                _flatten_form_fields("rubric_association", rubric_association)
            )
        return self._post(
            f"courses/{course_id}/rubrics",
            data=fields,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def delete_rubric(self, course_id: int, rubric_id: int) -> requests.Response:
        """Delete a rubric and its associations."""
        return self._delete(f"courses/{course_id}/rubrics/{rubric_id}")

    def attach_rubric_to_assignment(self, course_id: int, rubric_id: int, assignment_id: int,
                                     use_for_grading: bool = True) -> dict:
        """Attach a rubric to an assignment via rubric association."""
        data = {
            "rubric_association": {
                "rubric_id": rubric_id,
                "association_id": assignment_id,
                "association_type": "Assignment",
                "use_for_grading": use_for_grading,
                "purpose": "grading"
            }
        }
        return self._post(f"courses/{course_id}/rubric_associations", json=data)

    def delete_rubric_association(self, course_id: int,
                                  association_id: int) -> requests.Response:
        """Delete one rubric association without deleting the rubric."""
        return self._delete(
            f"courses/{course_id}/rubric_associations/{association_id}"
        )

    # ==================== Submissions ====================

    def get_submissions(self, course_id: int, assignment_id: int,
                        include_comments: bool = True) -> Iterator[dict]:
        """Get all submissions for an assignment."""
        params = {"per_page": 100}
        if include_comments:
            params["include[]"] = ["submission_comments", "user", "attachments"]
        return self._paginate(
            f"courses/{course_id}/assignments/{assignment_id}/submissions",
            params=params
        )

    def get_submission(self, course_id: int, assignment_id: int, user_id: int) -> dict:
        """Get a specific submission."""
        return self._get(
            f"courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}",
            params={"include[]": ["submission_comments", "user"]}
        )

    def update_submission(self, course_id: int, assignment_id: int, user_id: int,
                          grade: Optional[str] = None, comment: Optional[str] = None) -> dict:
        """Grade a submission and/or add a comment."""
        data = {"submission": {}}
        if grade is not None:
            data["submission"]["posted_grade"] = grade
        if comment is not None:
            data["comment"] = {"text_comment": comment}
        return self._put(
            f"courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}",
            json=data
        )

    # ==================== Discussions ====================

    def get_discussion_topics(self, course_id: int) -> Iterator[dict]:
        """Get all discussion topics in a course."""
        return self._paginate(f"courses/{course_id}/discussion_topics")

    def get_discussion_topic(self, course_id: int, topic_id: int) -> dict:
        """Get a specific discussion topic."""
        return self._get(f"courses/{course_id}/discussion_topics/{topic_id}")

    def update_discussion_topic(self, course_id: int, topic_id: int, **kwargs) -> dict:
        """Update a discussion topic."""
        return self._put(f"courses/{course_id}/discussion_topics/{topic_id}", json=kwargs)

    def update_checkpoints(self, topic_id: int, checkpoints: list) -> dict:
        """Update checkpoints via GraphQL (separate due dates/points for initial post vs replies).

        Each checkpoint dict should have:
          - tag: 'reply_to_topic' or 'reply_to_entry'
          - points_possible: float
          - due_at: ISO 8601 datetime string or None
        Optional for reply_to_entry: replies_required (int)
        """
        gql_checkpoints = []
        for cp in checkpoints:
            gql_cp = {
                "checkpointLabel": cp["tag"],
                "pointsPossible": cp["points_possible"],
                "dates": [{"type": "everyone", "dueAt": cp.get("due_at")}],
            }
            if cp["tag"] == "reply_to_entry" and cp.get("replies_required"):
                gql_cp["repliesRequired"] = cp["replies_required"]
            gql_checkpoints.append(gql_cp)

        query = """mutation UpdateDiscussion($input: UpdateDiscussionTopicInput!) {
            updateDiscussionTopic(input: $input) {
                discussionTopic { _id checkpoints { tag pointsPossible dueAt } }
                errors { message attribute }
            }
        }"""
        variables = {
            "input": {
                "discussionTopicId": str(topic_id),
                "setCheckpoints": True,
                "assignment": {"forCheckpoints": True},
                "checkpoints": gql_checkpoints,
            }
        }
        url = f"{self.base_url}/api/graphql"
        response = self.session.post(url, json={"query": query, "variables": variables})
        response.raise_for_status()
        result = response.json()
        if result.get("errors"):
            raise Exception(f"GraphQL errors: {result['errors']}")
        mutation_data = result.get("data", {}).get("updateDiscussionTopic", {})
        if mutation_data.get("errors"):
            raise Exception(f"Mutation errors: {mutation_data['errors']}")
        return mutation_data.get("discussionTopic", {})

    def disable_checkpoints(self, topic_id: int) -> dict:
        """Convert a checkpointed graded discussion back to one ordinary assignment.

        Canvas does not remove an obsolete reply checkpoint when a shorter
        checkpoint list is submitted. The GraphQL mutation must explicitly turn
        checkpoint mode off. Assignment dates and points should be set through the
        normal assignment update after this call.
        """
        query = """mutation UpdateDiscussion($input: UpdateDiscussionTopicInput!) {
            updateDiscussionTopic(input: $input) {
                discussionTopic { _id checkpoints { tag pointsPossible dueAt } replyToEntryRequiredCount }
                errors { message attribute }
            }
        }"""
        variables = {
            "input": {
                "discussionTopicId": str(topic_id),
                "setCheckpoints": False,
                "assignment": {"setAssignment": True, "forCheckpoints": False},
            }
        }
        url = f"{self.base_url}/api/graphql"
        response = self.session.post(url, json={"query": query, "variables": variables})
        response.raise_for_status()
        result = response.json()
        if result.get("errors"):
            raise Exception(f"GraphQL errors: {result['errors']}")
        mutation_data = result.get("data", {}).get("updateDiscussionTopic", {})
        if mutation_data.get("errors"):
            raise Exception(f"Mutation errors: {mutation_data['errors']}")
        return mutation_data.get("discussionTopic", {})

    def get_discussion_entries(self, course_id: int, topic_id: int) -> dict:
        """Get full discussion view with all entries and replies.

        Returns a dict with:
        - 'participants': list of user info dicts
        - 'view': list of top-level entry dicts, each with nested 'replies'
        """
        return self._get(f"courses/{course_id}/discussion_topics/{topic_id}/view")

    # ==================== Quizzes ====================

    def get_quizzes(self, course_id: int) -> Iterator[dict]:
        """Get all quizzes in a course."""
        return self._paginate(f"courses/{course_id}/quizzes")

    def get_quiz(self, course_id: int, quiz_id: int) -> dict:
        """Get a specific quiz."""
        return self._get(f"courses/{course_id}/quizzes/{quiz_id}")

    def get_quiz_questions(self, course_id: int, quiz_id: int) -> Iterator[dict]:
        """Get all questions in a quiz."""
        return self._paginate(f"courses/{course_id}/quizzes/{quiz_id}/questions")

    def update_quiz(self, course_id: int, quiz_id: int, **kwargs) -> dict:
        """Update a quiz."""
        return self._put(f"courses/{course_id}/quizzes/{quiz_id}", json={"quiz": kwargs})
