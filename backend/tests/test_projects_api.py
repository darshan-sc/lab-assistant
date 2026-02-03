"""
Test the Projects API endpoints via FastAPI TestClient.

Difficulty: 4/7
Introduces the `client` and `test_db` fixtures from conftest.py.
All requests go through the test client with auth overridden —
no real Supabase JWT is needed.

Run just this file:
    pytest tests/test_projects_api.py
"""

import pytest
from app.models.project import Project


class TestCreateProject:
    """POST /projects"""

    def test_create_project(self, client):
        """Creating a project should return 200 with project data."""
        # Example (filled in):
        resp = client.post("/projects", json={"name": "Test Project"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Project"
        assert "id" in data

    def test_create_project_with_description(self, client):
        # TODO: POST with name + description, verify both appear in response
        pass

    def test_create_project_empty_name_rejected(self, client):
        # TODO: POST with name="" should return 422
        pass

    def test_create_project_duplicate_name(self, client):
        # TODO: Create two projects with the same name —
        #       the second should fail (unique constraint on user_id + name)
        pass


class TestListProjects:
    """GET /projects"""

    def test_list_empty(self, client):
        # TODO: With no projects created, GET /projects should return []
        #       (or a list with just the auto-created "Default" project)
        pass

    def test_list_after_create(self, client):
        # TODO: Create a project, then GET /projects, verify it's in the list
        pass

    def test_list_pagination(self, client):
        # TODO: Create 5 projects, request with limit=2&offset=0,
        #       verify only 2 are returned
        pass


class TestGetProject:
    """GET /projects/{project_id}"""

    def test_get_existing(self, client):
        # TODO: Create a project, GET /projects/{id}, verify data matches
        pass

    def test_get_nonexistent(self, client):
        # TODO: GET /projects/99999 should return 404
        pass


class TestUpdateProject:
    """PATCH /projects/{project_id}"""

    def test_update_name(self, client):
        # TODO: Create project, PATCH with new name, verify response
        pass

    def test_update_description(self, client):
        # TODO: PATCH with only description, verify name unchanged
        pass

    def test_update_nonexistent(self, client):
        # TODO: PATCH /projects/99999 should return 404
        pass


class TestDeleteProject:
    """DELETE /projects/{project_id}"""

    def test_delete_project(self, client):
        # TODO: Create project, DELETE it, verify 200 response
        pass

    def test_delete_nonexistent(self, client):
        # TODO: DELETE /projects/99999 should return 404
        pass

    def test_delete_default_project_rejected(self, client):
        # TODO: The "Default" project cannot be deleted — verify the endpoint
        #       returns an error when you try.
        #       Hint: create a project named "Default" first (or trigger the
        #       auto-creation by hitting another endpoint).
        pass

    def test_get_after_delete_returns_404(self, client):
        # TODO: Create, delete, then GET — should be 404
        pass
