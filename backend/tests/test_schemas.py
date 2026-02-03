"""
Test Pydantic schemas for request/response validation.

Difficulty: 1/7 (easiest)
No database, no async, no mocking — just instantiate schemas and check
that validation passes or raises as expected.

Run just this file:
    pytest tests/test_schemas.py
"""

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from app.schemas.paper import PaperUpdate, PaperOut
from app.schemas.note import NoteCreate, NoteUpdate, NoteOut
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentOut,
    RunCreate,
    RunUpdate,
    RunOut,
)


# ---------------------------------------------------------------------------
# Example (filled in) — use this as a pattern for the TODOs below
# ---------------------------------------------------------------------------

class TestProjectSchemas:
    """Validate ProjectCreate / ProjectUpdate / ProjectOut."""

    def test_project_create_valid(self):
        """A minimal valid ProjectCreate should work."""
        p = ProjectCreate(name="My Project")
        assert p.name == "My Project"
        assert p.description is None

    def test_project_create_with_description(self):
        p = ProjectCreate(name="P", description="Some desc")
        assert p.description == "Some desc"

    def test_project_create_empty_name_rejected(self):
        """name has min_length=1, so an empty string should fail."""
        with pytest.raises(ValidationError):
            ProjectCreate(name="")

    def test_project_create_long_name_rejected(self):
        """name has max_length=200."""
        with pytest.raises(ValidationError):
            ProjectCreate(name="x" * 201)

    def test_project_update_all_none(self):
        """ProjectUpdate with no fields is valid (partial update)."""
        # TODO: Instantiate ProjectUpdate() with no args, assert fields are None
        pass

    def test_project_out_from_attributes(self):
        """ProjectOut should accept from_attributes (ORM mode)."""
        # TODO: Create a ProjectOut using model_validate() with a dict that
        #       includes id, user_id, name, created_at, updated_at.
        pass


class TestPaperSchemas:
    """Validate PaperUpdate / PaperOut."""

    def test_paper_update_valid(self):
        # TODO: Create PaperUpdate with a title, assert it round-trips
        pass

    def test_paper_update_empty_title_rejected(self):
        # TODO: PaperUpdate(title="") should raise ValidationError (min_length=1)
        pass

    def test_paper_out_defaults(self):
        # TODO: PaperOut should default is_indexed_for_rag to False
        pass


class TestNoteSchemas:
    """Validate NoteCreate / NoteUpdate / NoteOut."""

    def test_note_create_content_required(self):
        # TODO: NoteCreate without content should raise ValidationError
        pass

    def test_note_create_optional_links(self):
        # TODO: NoteCreate(content="x") should have None for project_id, paper_id, etc.
        pass

    def test_note_update_partial(self):
        # TODO: NoteUpdate() with no args should be valid
        pass


class TestExperimentSchemas:
    """Validate Experiment and Run schemas."""

    def test_experiment_create_valid(self):
        # TODO: ExperimentCreate(title="Exp 1") should work
        pass

    def test_experiment_create_empty_title_rejected(self):
        # TODO: ExperimentCreate(title="") should fail (min_length=1)
        pass

    def test_experiment_create_long_title_rejected(self):
        # TODO: title max_length=300
        pass

    def test_run_create_defaults(self):
        # TODO: RunCreate() with no args should be valid (all optional)
        pass

    def test_run_update_partial(self):
        # TODO: RunUpdate() with no args should be valid
        pass

    def test_run_create_with_config(self):
        # TODO: RunCreate(config={"lr": 0.01, "epochs": 10}) should work
        pass
