"""Parity tests for the committed DSP golden vectors.

These tests guard the contract enforced by ``scripts/benchmark.py``:
the output of every benchmarked DSP stage on a fixed deterministic
input must match the reference arrays committed under
``tests/golden/`` to within ~1 LSB at single precision.

If a code change in ``dsp/`` is intentional, regenerate the golden
vectors with::

    python -m scripts.benchmark --regen-golden

and commit the diff.  Silent regeneration is by design impossible —
this test will fail and explain how to proceed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from scripts.benchmark import STAGE_FACTORIES, _run_stage_on_frames

GOLDEN_DIR = Path(__file__).parent / "golden"


def _all_present() -> bool:
    return (GOLDEN_DIR / "input.npy").exists() and all(
        (GOLDEN_DIR / f"{name}.npy").exists() for name in STAGE_FACTORIES
    )


pytestmark = pytest.mark.skipif(
    not _all_present(),
    reason=(
        "Golden vectors not present.  Run "
        "`python -m scripts.benchmark --regen-golden` to create them."
    ),
)


@pytest.fixture(scope="module")
def golden_input() -> np.ndarray:
    return np.load(GOLDEN_DIR / "input.npy")


@pytest.mark.parametrize("stage_name", list(STAGE_FACTORIES.keys()))
def test_stage_matches_golden(stage_name: str, golden_input: np.ndarray) -> None:
    expected = np.load(GOLDEN_DIR / f"{stage_name}.npy")
    actual = _run_stage_on_frames(stage_name, golden_input)
    assert actual.shape == expected.shape
    if not np.allclose(actual, expected, atol=1e-5, rtol=0.0):
        max_err = float(np.max(np.abs(actual - expected)))
        pytest.fail(
            f"Golden-vector drift in stage '{stage_name}': "
            f"max_abs_err={max_err:.3e}.\n"
            "If this change is intentional, regenerate the vectors with "
            "`python -m scripts.benchmark --regen-golden` and commit the diff."
        )


def test_input_vector_is_stable(golden_input: np.ndarray) -> None:
    """The input vector itself must be reproducible from the same seed."""
    from scripts.benchmark import _golden_input

    regenerated = _golden_input(golden_input.shape[1])
    np.testing.assert_array_equal(golden_input, regenerated)
