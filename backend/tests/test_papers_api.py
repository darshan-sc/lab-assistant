"""
Test the Papers API endpoints via FastAPI TestClient.

Difficulty: 6/7
Adds file-upload testing with multipart form data.
The upload endpoint triggers async processing (PDF extraction, LLM calls),
so you may need to mock those services or test only the HTTP layer.

Run just this file:
    pytest tests/test_papers_api.py

Tip: For upload tests, use `client.post("/papers/upload", files={"file": ...})`
     with an in-memory PDF (see test_pdf_extractor.py for _make_sample_pdf).
"""

import pytest
from unittest.mock import patch, AsyncMock


# ---------------------------------------------------------------------------
# Helper: create a minimal PDF in memory
# ---------------------------------------------------------------------------
def _make_sample_pdf(pages: list[str]) -> bytes:
    """Create a PDF with the given page texts. Requires PyMuPDF (fitz)."""
    import fitz

    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


class TestUploadPaper:
    """POST /papers/upload"""

    def test_upload_pdf(self, client):
        # TODO: Upload a sample PDF using multipart form data.
        #       You'll likely need to mock the background services
        #       (extract_paper_metadata, parse_document_sections, index_paper_with_sections)
        #       since they call external APIs.
        #
        #       Example skeleton:
        #
        #       pdf_bytes = _make_sample_pdf(["Sample paper text"])
        #       with patch("app.api.routes.papers.extract_paper_metadata", new_callable=AsyncMock) as mock_meta, \
        #            patch("app.api.routes.papers.parse_document_sections", new_callable=AsyncMock) as mock_sections, \
        #            patch("app.api.routes.papers.index_paper_with_sections", new_callable=AsyncMock) as mock_index:
        #           mock_meta.return_value = {"title": "Test Paper", "abstract": "An abstract"}
        #           mock_sections.return_value = []
        #           mock_index.return_value = 5  # chunks created
        #
        #           resp = client.post(
        #               "/papers/upload",
        #               files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        #           )
        #           assert resp.status_code == 200
        pass

    def test_upload_non_pdf_rejected(self, client):
        # TODO: Upload a .txt file — should the endpoint reject it?
        #       Check the actual endpoint logic for file-type validation.
        pass


class TestListPapers:
    """GET /papers"""

    def test_list_empty(self, client):
        # TODO: GET /papers with no papers uploaded should return []
        pass

    def test_list_filter_by_project(self, client):
        # TODO: Upload papers to different projects, filter by project_id
        pass


class TestGetPaper:
    """GET /papers/{paper_id}"""

    def test_get_existing(self, client):
        # TODO: Upload a paper, GET by id, verify response matches
        pass

    def test_get_nonexistent(self, client):
        # TODO: GET /papers/99999 should return 404
        pass


class TestUpdatePaper:
    """PATCH /papers/{paper_id}"""

    def test_update_title(self, client):
        # TODO: Upload, then PATCH with new title, verify response
        pass

    def test_update_nonexistent(self, client):
        # TODO: PATCH /papers/99999 should return 404
        pass


class TestDeletePaper:
    """DELETE /papers/{paper_id}"""

    def test_delete_paper(self, client):
        # TODO: Upload, delete, verify 200
        pass

    def test_delete_nonexistent(self, client):
        # TODO: DELETE /papers/99999 should return 404
        pass

    def test_delete_cascades_to_notes(self, client):
        # TODO: Create a paper, add a note linked to it, delete the paper,
        #       verify the note is also gone.
        pass
