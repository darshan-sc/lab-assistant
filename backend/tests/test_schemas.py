"""
Test Pydantic schemas for request/response validation.

Run just this file:
    pytest tests/test_schemas.py
"""

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreate


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
