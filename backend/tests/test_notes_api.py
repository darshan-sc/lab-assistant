"""
Test the Notes API endpoints via FastAPI TestClient.

Difficulty: 5/7
Same CRUD pattern as projects, good practice for the TestClient workflow.
Notes can optionally link to papers, experiments, or runs.

Run just this file:
    pytest tests/test_notes_api.py
"""

import pytest


class TestCreateNote:
    """POST /notes"""

    def test_create_note(self, client):
        """Creating a note with just content should succeed."""
        # Example (filled in):
        resp = client.post("/notes", json={"content": "My first note"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["content"] == "My first note"
        assert "id" in data

    def test_create_note_with_project(self, client):
        # TODO: Create a project first, then create a note with that project_id.
        #       Verify the note's project_id matches.
        pass

    def test_create_note_missing_content(self, client):
        # TODO: POST /notes with no content field should return 422
        pass


class TestListNotes:
    """GET /notes"""

    def test_list_empty(self, client):
        # TODO: GET /notes with nothing created should return []
        pass

    def test_list_filter_by_project(self, client):
        # TODO: Create notes in two projects, filter by project_id,
        #       verify only the correct ones are returned
        pass

    def test_list_pagination(self, client):
        # TODO: Create several notes, use limit and offset params
        pass


class TestUpdateNote:
    """PATCH /notes/{note_id}"""

    def test_update_content(self, client):
        # TODO: Create a note, PATCH with new content, verify response
        pass

    def test_update_nonexistent(self, client):
        # TODO: PATCH /notes/99999 should return 404
        pass


class TestDeleteNote:
    """DELETE /notes/{note_id}"""

    def test_delete_note(self, client):
        # TODO: Create, delete, verify 200
        pass

    def test_delete_nonexistent(self, client):
        # TODO: DELETE /notes/99999 should return 404
        pass

    def test_get_after_delete(self, client):
        # TODO: After deleting, verify the note no longer appears in GET /notes
        pass
