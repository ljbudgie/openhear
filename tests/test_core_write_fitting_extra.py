"""Additional tests for ``core/write_fitting.py`` – validation edge cases
not covered by the main test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.fitting_data import DeviceInfo, FittingSession
from core.write_fitting import (
    ALLOWED_PARAMETERS,
    WriteRequest,
    _apply_request_to_session,
    _validate_request,
    write_safe_parameters,
)


def _make_session() -> FittingSession:
    return FittingSession(device=DeviceInfo(serial="SN001"))


class TestValidateRequestProgrammeName:
    def test_valid_name_does_not_raise(self):
        req = WriteRequest(programme_slot=0, parameter="programme_name", value="General")
        _validate_request(req)  # should not raise

    def test_empty_name_raises(self):
        req = WriteRequest(programme_slot=0, parameter="programme_name", value="   ")
        with pytest.raises(ValueError, match="non-empty"):
            _validate_request(req)

    def test_non_string_raises(self):
        req = WriteRequest(programme_slot=0, parameter="programme_name", value=123)
        with pytest.raises(ValueError, match="non-empty"):
            _validate_request(req)

    def test_name_too_long_raises(self):
        req = WriteRequest(programme_slot=0, parameter="programme_name", value="x" * 33)
        with pytest.raises(ValueError, match="32 characters"):
            _validate_request(req)

    def test_name_exactly_32_chars_ok(self):
        req = WriteRequest(programme_slot=0, parameter="programme_name", value="a" * 32)
        _validate_request(req)  # should not raise


class TestValidateRequestVolumeOffset:
    def test_valid_zero(self):
        req = WriteRequest(programme_slot=0, parameter="volume_offset_db", value=0.0)
        _validate_request(req)

    def test_non_numeric_raises(self):
        req = WriteRequest(programme_slot=0, parameter="volume_offset_db", value="loud")
        with pytest.raises(ValueError, match="number"):
            _validate_request(req)

    def test_above_max_raises(self):
        req = WriteRequest(programme_slot=0, parameter="volume_offset_db", value=13.0)
        with pytest.raises(ValueError, match="\\[-12"):
            _validate_request(req)

    def test_below_min_raises(self):
        req = WriteRequest(programme_slot=0, parameter="volume_offset_db", value=-13.0)
        with pytest.raises(ValueError, match="\\[-12"):
            _validate_request(req)

    def test_boundary_values_accepted(self):
        for v in (-12.0, 12.0):
            req = WriteRequest(programme_slot=0, parameter="volume_offset_db", value=v)
            _validate_request(req)


class TestValidateRequestStreamingPreference:
    def test_valid_values(self):
        for v in ("automatic", "priority", "off"):
            req = WriteRequest(programme_slot=0, parameter="streaming_preference", value=v)
            _validate_request(req)

    def test_invalid_value_raises(self):
        req = WriteRequest(programme_slot=0, parameter="streaming_preference", value="always")
        with pytest.raises(ValueError, match="streaming_preference"):
            _validate_request(req)


class TestValidateRequestDisallowedParameter:
    def test_gain_table_is_refused(self):
        req = WriteRequest(programme_slot=0, parameter="gain_table", value=[])
        with pytest.raises(PermissionError, match="gain_table"):
            _validate_request(req)

    def test_mpo_limit_is_refused(self):
        req = WriteRequest(programme_slot=0, parameter="mpo_limit_db", value=100)
        with pytest.raises(PermissionError, match="mpo_limit_db"):
            _validate_request(req)


class TestApplyRequestToSession:
    def test_sets_programme_name(self):
        session = _make_session()
        req = WriteRequest(programme_slot=0, parameter="programme_name", value="Music")
        _apply_request_to_session(session, req)
        assert session.programmes[0].name == "Music"

    def test_sets_volume_offset(self):
        session = _make_session()
        req = WriteRequest(programme_slot=0, parameter="volume_offset_db", value=3.0)
        _apply_request_to_session(session, req)
        assert session.programmes[0].volume_offset_db == pytest.approx(3.0)

    def test_sets_streaming_preference(self):
        session = _make_session()
        req = WriteRequest(programme_slot=0, parameter="streaming_preference", value="priority")
        _apply_request_to_session(session, req)
        assert session.programmes[0].streaming_preference == "priority"

    def test_creates_slot_when_not_present(self):
        session = _make_session()
        assert len(session.programmes) == 0
        req = WriteRequest(programme_slot=5, parameter="programme_name", value="Noise")
        _apply_request_to_session(session, req)
        assert len(session.programmes) == 1
        assert session.programmes[0].slot_index == 5
        assert session.programmes[0].name == "Noise"


class TestWriteSafeParameters:
    def test_empty_requests_raises(self, tmp_path):
        session = _make_session()
        with pytest.raises(ValueError, match="least one"):
            write_safe_parameters(
                session, b"raw", [], backup_dir=tmp_path,
            )

    def test_returns_backup_archive(self, tmp_path):
        session = _make_session()
        req = WriteRequest(programme_slot=0, parameter="programme_name", value="Test")
        archive = write_safe_parameters(
            session, b"rawbytes", [req], backup_dir=tmp_path,
        )
        assert archive.fitting_path.exists()
        assert archive.raw_path.exists()
        assert archive.manifest_path.exists()

    def test_transmit_true_raises_not_implemented(self, tmp_path):
        session = _make_session()
        req = WriteRequest(programme_slot=0, parameter="programme_name", value="Env")
        with pytest.raises(NotImplementedError):
            write_safe_parameters(
                session, b"raw", [req], backup_dir=tmp_path, transmit=True,
            )

    def test_disallowed_parameter_raises_before_backup(self, tmp_path):
        session = _make_session()
        req = WriteRequest(programme_slot=0, parameter="gain_table", value=[])
        with pytest.raises(PermissionError):
            write_safe_parameters(session, b"raw", [req], backup_dir=tmp_path)
        # Backup directory should NOT have been written yet.
        assert not any(tmp_path.iterdir())

    def test_multiple_requests_applied(self, tmp_path):
        session = _make_session()
        reqs = [
            WriteRequest(programme_slot=0, parameter="programme_name", value="P1"),
            WriteRequest(programme_slot=1, parameter="volume_offset_db", value=2.0),
        ]
        write_safe_parameters(session, b"data", reqs, backup_dir=tmp_path)
        assert session.programmes[0].name == "P1"
        assert session.programmes[1].volume_offset_db == pytest.approx(2.0)
