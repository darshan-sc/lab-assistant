"""
Test the Experiments and Experiment Runs API endpoints.

Difficulty: 7/7 (hardest)
Nested resources: experiments live under projects, runs live under experiments.
Tests need to create a project first, then experiments, then runs.

Run just this file:
    pytest tests/test_experiments_api.py
"""

import pytest


# ---------------------------------------------------------------------------
# Helper fixture: create a project to host experiments
# ---------------------------------------------------------------------------

@pytest.fixture()
def project_id(client) -> int:
    """Create a project and return its id for use in experiment tests."""
    resp = client.post("/projects", json={"name": "Exp Test Project"})
    assert resp.status_code == 200
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Experiment CRUD
# ---------------------------------------------------------------------------

class TestCreateExperiment:
    """POST /projects/{project_id}/experiments"""

    def test_create_experiment(self, client, project_id):
        """Creating an experiment should return 200 with experiment data."""
        # Example (filled in):
        resp = client.post(
            f"/projects/{project_id}/experiments",
            json={"title": "Exp 1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Exp 1"
        assert data["status"] == "active"

    def test_create_with_optional_fields(self, client, project_id):
        # TODO: Create with goal, protocol, and paper_id (if applicable).
        #       Verify all fields appear in response.
        pass

    def test_create_empty_title_rejected(self, client, project_id):
        # TODO: POST with title="" should return 422
        pass

    def test_create_in_nonexistent_project(self, client):
        # TODO: POST /projects/99999/experiments should return 404
        pass


class TestListExperiments:
    """GET /projects/{project_id}/experiments"""

    def test_list_empty(self, client, project_id):
        # TODO: No experiments created yet — should return []
        pass

    def test_list_after_create(self, client, project_id):
        # TODO: Create an experiment, then list, verify it's present
        pass

    def test_list_pagination(self, client, project_id):
        # TODO: Create several experiments, use limit/offset
        pass


class TestGetExperiment:
    """GET /experiments/{experiment_id}"""

    def test_get_existing(self, client, project_id):
        # TODO: Create, then GET, verify data matches
        pass

    def test_get_nonexistent(self, client):
        # TODO: GET /experiments/99999 should return 404
        pass


class TestUpdateExperiment:
    """PATCH /experiments/{experiment_id}"""

    def test_update_title(self, client, project_id):
        # TODO: Create, PATCH with new title, verify
        pass

    def test_update_status(self, client, project_id):
        # TODO: PATCH with status="completed", verify
        pass

    def test_update_nonexistent(self, client):
        # TODO: PATCH /experiments/99999 should return 404
        pass


class TestDeleteExperiment:
    """DELETE /experiments/{experiment_id}"""

    def test_delete_experiment(self, client, project_id):
        # TODO: Create, delete, verify 200
        pass

    def test_delete_nonexistent(self, client):
        # TODO: DELETE /experiments/99999 should return 404
        pass

    def test_delete_cascades_to_runs(self, client, project_id):
        # TODO: Create experiment + runs, delete experiment,
        #       verify runs are also gone.
        pass


# ---------------------------------------------------------------------------
# Experiment Run CRUD
# ---------------------------------------------------------------------------

@pytest.fixture()
def experiment_id(client, project_id) -> int:
    """Create an experiment and return its id for use in run tests."""
    resp = client.post(
        f"/projects/{project_id}/experiments",
        json={"title": "Run Test Experiment"},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


class TestCreateRun:
    """POST /experiments/{experiment_id}/runs"""

    def test_create_run(self, client, experiment_id):
        # TODO: POST with run_name and config, verify response
        pass

    def test_create_run_defaults(self, client, experiment_id):
        # TODO: POST with empty body {}, verify status defaults to "planned"
        pass

    def test_create_run_in_nonexistent_experiment(self, client):
        # TODO: POST /experiments/99999/runs should return 404
        pass


class TestListRuns:
    """GET /experiments/{experiment_id}/runs"""

    def test_list_empty(self, client, experiment_id):
        # TODO: No runs yet — should return []
        pass

    def test_list_after_create(self, client, experiment_id):
        # TODO: Create a run, list, verify
        pass


class TestGetRun:
    """GET /runs/{run_id}"""

    def test_get_existing(self, client, experiment_id):
        # TODO: Create, GET, verify
        pass

    def test_get_nonexistent(self, client):
        # TODO: GET /runs/99999 should return 404
        pass


class TestUpdateRun:
    """PATCH /runs/{run_id}"""

    def test_update_status(self, client, experiment_id):
        # TODO: PATCH with status="running", verify
        pass

    def test_update_metrics(self, client, experiment_id):
        # TODO: PATCH with metrics={"acc": 0.95}, verify
        pass

    def test_update_nonexistent(self, client):
        # TODO: PATCH /runs/99999 should return 404
        pass


class TestDeleteRun:
    """DELETE /runs/{run_id}"""

    def test_delete_run(self, client, experiment_id):
        # TODO: Create, delete, verify 200
        pass

    def test_delete_nonexistent(self, client):
        # TODO: DELETE /runs/99999 should return 404
        pass
