"""Tests for the OCR-import audiogram stub."""

from __future__ import annotations

import pytest

from audiogram.import_pdf import import_pdf


def test_import_pdf_raises_with_helpful_message(tmp_path):
    with pytest.raises(NotImplementedError) as excinfo:
        import_pdf(tmp_path / "audiogram.pdf")
    msg = str(excinfo.value)
    assert "not yet implemented" in msg
    # Pointer to the workaround should be mentioned.
    assert "manual_entry" in msg


def test_import_pdf_accepts_string_path():
    with pytest.raises(NotImplementedError):
        import_pdf("any.pdf")
