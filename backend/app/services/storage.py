from __future__ import annotations

from pathlib import Path
import uuid

from app.core.config import settings


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_upload_pdf(file_bytes: bytes, original_filename: str) -> str:
    """
    Save an uploaded PDF to disk under STORAGE_DIR/papers/.
    Returns the saved file path as a string (store this in Paper.pdf_path for now).
    """

    if not file_bytes:
        raise ValueError("Empty file")

    # Avoid weird filenames / path traversal; we only keep the suffix if it's .pdf
    suffix = Path(original_filename).suffix.lower()
    if suffix != ".pdf":
        suffix = ".pdf"

    base_dir = Path(settings.STORAGE_DIR)
    papers_dir = base_dir / "papers"
    _ensure_dir(papers_dir)

    # Unique server-side filename
    filename = f"{uuid.uuid4().hex}{suffix}"
    out_path = papers_dir / filename

    out_path.write_bytes(file_bytes)

    # Return a path you can store. (Later you can store a key like f"papers/{filename}")
    return str(out_path)
