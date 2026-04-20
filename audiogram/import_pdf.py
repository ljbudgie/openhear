"""
import_pdf.py – stub for OCR import of paper/PDF audiograms (Phase 2).

Many users receive their audiogram as a printed chart or scanned PDF.
The plan is to use image processing to extract threshold values from a
photograph or scan of a clinical audiogram and emit an
``openhear-audiogram-v1`` JSON file ready for the rest of OpenHear.

Planned approach (not yet implemented):

1. Detect the audiogram chart bounds (template matching against the
   common layouts used by Phonak Target, Connexx, Audacity, etc.).
2. Locate the X (left ear) and O (right ear) markers via colour
   segmentation and shape detection.
3. Map each marker's pixel coordinates back to (frequency, dB HL) using
   the chart's calibrated axes.
4. Validate against the standard frequency set
   (:data:`audiogram.audiogram.STANDARD_FREQUENCIES_HZ`) and emit a
   :class:`audiogram.audiogram.Audiogram`.

Until that work lands, this module exposes :func:`import_pdf` purely as
a documented placeholder so callers fail loudly with a clear message
rather than silently misbehaving.
"""

from __future__ import annotations

from pathlib import Path

from audiogram.audiogram import Audiogram


def import_pdf(path: str | Path) -> Audiogram:
    """Stub: extract an audiogram from a PDF or image file.

    Args:
        path: Path to the PDF, PNG, or JPEG to import.

    Returns:
        An :class:`Audiogram` once the OCR pipeline is implemented.

    Raises:
        NotImplementedError: Always — this is a Phase 2 deliverable.
    """
    raise NotImplementedError(
        "OCR import of audiograms is not yet implemented; see the module "
        "docstring for the planned approach.  In the meantime, use "
        "`python -m audiogram.manual_entry --output AG.json` to enter "
        "the thresholds from your paper audiogram by hand."
    )
