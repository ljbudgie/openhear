"""Tests for :mod:`dsp.fatigue` and :mod:`dsp.fatigue_cli`."""

from __future__ import annotations

import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout

import pytest

from dsp import fatigue, fatigue_cli
from dsp.contact_profiles import ContactBank, ContactProfile, save_bank
from dsp.fatigue import (
    DEFAULT_GREEN_FLOOR,
    DEFAULT_RED_CEILING,
    RECOVERY_FILE_ENV_VAR,
    RecoveryBucket,
    WhoopRecovery,
    bucket,
    default_recovery_path,
    fatigue_bias,
    fatigue_delta_from_file,
    forget_recovery,
    read_recovery,
    write_recovery,
)
from dsp.profile_delta import ProfileDelta

# ── Bucket boundaries (§9 Q3 thresholds) ────────────────────────────────────


class TestBucket:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (100, RecoveryBucket.GREEN),
            (67, RecoveryBucket.GREEN),
            (66, RecoveryBucket.YELLOW),
            (50, RecoveryBucket.YELLOW),
            (34, RecoveryBucket.YELLOW),
            (33, RecoveryBucket.RED),
            (0, RecoveryBucket.RED),
        ],
    )
    def test_default_thresholds(self, score, expected):
        assert bucket(score) is expected

    def test_none_is_unknown(self):
        assert bucket(None) is RecoveryBucket.UNKNOWN

    def test_out_of_range_is_unknown(self, caplog):
        with caplog.at_level("WARNING"):
            assert bucket(150) is RecoveryBucket.UNKNOWN
            assert bucket(-5) is RecoveryBucket.UNKNOWN

    def test_non_numeric_is_unknown(self, caplog):
        with caplog.at_level("WARNING"):
            assert bucket("not-a-number") is RecoveryBucket.UNKNOWN  # type: ignore[arg-type]

    def test_custom_thresholds_apply(self):
        assert bucket(50, green_floor=80, red_ceiling=20) is RecoveryBucket.YELLOW
        assert bucket(85, green_floor=80, red_ceiling=20) is RecoveryBucket.GREEN

    def test_inverted_thresholds_rejected(self):
        with pytest.raises(ValueError):
            bucket(50, green_floor=30, red_ceiling=70)

    def test_overlapping_thresholds_rejected(self):
        with pytest.raises(ValueError):
            bucket(50, green_floor=50, red_ceiling=50)


# ── FatigueBias contents ────────────────────────────────────────────────────


class TestFatigueBias:
    def test_green_identity_no_suggestion(self):
        bias = fatigue_bias(RecoveryBucket.GREEN, source_score=80)
        assert bias.delta.is_identity()
        assert bias.suggest_low_effort_preset is False
        assert "no fatigue bias" in bias.explanation

    def test_unknown_identity_no_suggestion(self):
        bias = fatigue_bias(RecoveryBucket.UNKNOWN)
        assert bias.delta.is_identity()
        assert bias.suggest_low_effort_preset is False
        assert "unknown" in bias.explanation.lower()

    def test_yellow_mild_bias_no_suggestion(self):
        bias = fatigue_bias(RecoveryBucket.YELLOW, source_score=50)
        assert not bias.delta.is_identity()
        assert bias.delta.compression_ratio_delta < 0  # softer
        assert bias.delta.nr_aggressiveness_delta < 0  # gentler NR
        assert bias.suggest_low_effort_preset is False
        assert "fatigue:yellow" in bias.delta.sources

    def test_red_strong_bias_with_suggestion(self):
        bias = fatigue_bias(RecoveryBucket.RED, source_score=20)
        assert not bias.delta.is_identity()
        assert bias.suggest_low_effort_preset is True
        assert "fatigue:red" in bias.delta.sources
        # Burgess: SUGGESTING not auto-applying.
        assert "SUGGESTING" in bias.explanation

    def test_red_bias_stronger_than_yellow(self):
        y = fatigue_bias(RecoveryBucket.YELLOW).delta
        r = fatigue_bias(RecoveryBucket.RED).delta
        assert abs(r.compression_ratio_delta) > abs(y.compression_ratio_delta)
        assert abs(r.nr_aggressiveness_delta) > abs(y.nr_aggressiveness_delta)

    def test_red_bias_within_safe_envelope(self):
        from dsp.profile_delta import (
            MAX_COMPRESSION_KNEE_DELTA_DB,
            MAX_COMPRESSION_RATIO_DELTA,
            MAX_NR_AGGRESSIVENESS_DELTA,
            MAX_VOICE_GAIN_DELTA,
        )

        r = fatigue_bias(RecoveryBucket.RED).delta
        assert abs(r.compression_ratio_delta) <= MAX_COMPRESSION_RATIO_DELTA
        assert abs(r.compression_knee_delta_db) <= MAX_COMPRESSION_KNEE_DELTA_DB
        assert abs(r.voice_gain_delta) <= MAX_VOICE_GAIN_DELTA
        assert abs(r.nr_aggressiveness_delta) <= MAX_NR_AGGRESSIVENESS_DELTA


# ── File round-trip + path resolution ───────────────────────────────────────


class TestRecoveryFile:
    def test_default_path_under_home(self):
        p = default_recovery_path()
        assert p.name == "whoop_recovery.json"
        assert p.parent.name == ".openhear"

    def test_read_missing_returns_none(self, tmp_path):
        assert read_recovery(tmp_path / "nope.json") is None

    def test_write_read_round_trip(self, tmp_path):
        path = tmp_path / "r.json"
        write_recovery(WhoopRecovery(score=42, timestamp="t", source="manual"), path)
        r = read_recovery(path)
        assert r is not None
        assert r.score == 42
        assert r.timestamp == "t"
        assert r.source == "manual"

    def test_env_var_override(self, tmp_path, monkeypatch):
        path = tmp_path / "from_env.json"
        write_recovery(WhoopRecovery(score=80), path)
        monkeypatch.setenv(RECOVERY_FILE_ENV_VAR, str(path))
        r = read_recovery()
        assert r is not None and r.score == 80

    def test_explicit_path_overrides_env(self, tmp_path, monkeypatch):
        env_path = tmp_path / "env.json"
        write_recovery(WhoopRecovery(score=80), env_path)
        explicit_path = tmp_path / "explicit.json"
        write_recovery(WhoopRecovery(score=20), explicit_path)
        monkeypatch.setenv(RECOVERY_FILE_ENV_VAR, str(env_path))
        r = read_recovery(explicit_path)
        assert r is not None and r.score == 20

    def test_malformed_score_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"score": "abc"}))
        with pytest.raises(ValueError):
            read_recovery(path)

    def test_out_of_range_score_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"score": 150}))
        with pytest.raises(ValueError):
            read_recovery(path)

    def test_missing_score_field_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps({"timestamp": "t"}))
        with pytest.raises(ValueError, match="score"):
            read_recovery(path)

    def test_non_object_root_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(ValueError):
            read_recovery(path)

    def test_empty_file_returns_none(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text("")
        assert read_recovery(path) is None

    def test_forget_deletes(self, tmp_path):
        path = tmp_path / "r.json"
        write_recovery(WhoopRecovery(score=50), path)
        assert path.exists()
        assert forget_recovery(path) is True
        assert not path.exists()
        # Idempotent.
        assert forget_recovery(path) is False

    def test_write_uses_safe_modes(self, tmp_path):
        path = tmp_path / "nested" / "r.json"
        write_recovery(WhoopRecovery(score=50), path)
        assert path.exists()
        # POSIX permissions check (best-effort; skip on other filesystems).
        if os.name == "posix":
            assert (path.stat().st_mode & 0o777) == 0o600


# ── fatigue_delta_from_file: disabled by default + composition ──────────────


class TestFatigueDeltaFromFile:
    def test_missing_file_returns_identity(self, tmp_path):
        assert fatigue_delta_from_file(tmp_path / "no.json").is_identity()

    def test_malformed_file_returns_identity_with_warning(self, tmp_path, caplog):
        path = tmp_path / "bad.json"
        path.write_text("not json{{")
        with caplog.at_level("WARNING"):
            d = fatigue_delta_from_file(path)
        assert d.is_identity()
        assert any("recovery" in r.message.lower() for r in caplog.records)

    def test_green_returns_identity(self, tmp_path):
        path = tmp_path / "r.json"
        write_recovery(WhoopRecovery(score=80), path)
        assert fatigue_delta_from_file(path).is_identity()

    def test_yellow_returns_mild_bias(self, tmp_path, caplog):
        path = tmp_path / "r.json"
        write_recovery(WhoopRecovery(score=50), path)
        with caplog.at_level("INFO"):
            d = fatigue_delta_from_file(path)
        assert not d.is_identity()
        assert "fatigue:yellow" in d.sources
        assert any("BGSP|fatigue-bias-applied" in r.message for r in caplog.records)

    def test_red_returns_bias_and_logs_suggestion(self, tmp_path, caplog):
        path = tmp_path / "r.json"
        write_recovery(WhoopRecovery(score=20), path)
        with caplog.at_level("WARNING"):
            d = fatigue_delta_from_file(path)
        assert "fatigue:red" in d.sources
        assert any("BGSP|fatigue-low-effort-suggested" in r.message for r in caplog.records)

    def test_custom_thresholds_change_classification(self, tmp_path):
        path = tmp_path / "r.json"
        write_recovery(WhoopRecovery(score=50), path)
        # With a higher green_floor, score=50 is now red instead of yellow.
        d_strict = fatigue_delta_from_file(path, green_floor=80, red_ceiling=60)
        assert "fatigue:red" in d_strict.sources


# ── Composition order with ContactProfile (Phase 1 + Phase 2 together) ──────


class TestCompositionOrder:
    def test_contact_then_fatigue_compose_cleanly(self, tmp_path):
        # Build a contact delta and a fatigue delta and combine.
        contact = ProfileDelta(voice_gain_delta=0.1, sources=("contact:partner",), reason="contact")
        # Score=50 → yellow → mild bias.
        path = tmp_path / "r.json"
        write_recovery(WhoopRecovery(score=50), path)
        fatigue_d = fatigue_delta_from_file(path)
        combined = ProfileDelta.compose([contact, fatigue_d])
        # Voice gain delta should be contact (+0.1) + yellow (-0.05) = +0.05.
        assert combined.voice_gain_delta == pytest.approx(0.05)
        # Sources include both, in order.
        assert combined.sources[0] == "contact:partner"
        assert combined.sources[1] == "fatigue:yellow"

    def test_pipeline_resolves_both_sources(self, tmp_path):
        from dsp.pipeline import _resolve_runtime_delta

        contacts = tmp_path / "contacts.json"
        bank = ContactBank()
        bank.add(ContactProfile(contact_id="partner", consent=True, voice_gain_delta=0.1))
        save_bank(bank, contacts)
        recovery_path = tmp_path / "r.json"
        write_recovery(WhoopRecovery(score=50), recovery_path)

        d = _resolve_runtime_delta(
            contact_id="partner",
            contacts_path=str(contacts),
            fatigue_enabled=True,
            fatigue_recovery_file=str(recovery_path),
        )
        assert "contact:partner" in d.sources
        assert "fatigue:yellow" in d.sources

    def test_pipeline_fatigue_disabled_skips_file(self, tmp_path):
        from dsp.pipeline import _resolve_runtime_delta

        # Even with a recovery file present, fatigue_enabled=False ignores it.
        recovery_path = tmp_path / "r.json"
        write_recovery(WhoopRecovery(score=20), recovery_path)
        d = _resolve_runtime_delta(fatigue_enabled=False, fatigue_recovery_file=str(recovery_path))
        assert d.is_identity()


# ── CLI ─────────────────────────────────────────────────────────────────────


class TestCLI:
    def _run(self, argv, *, expect_status=0):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = fatigue_cli.main(argv)
        assert rc == expect_status, (rc, out.getvalue(), err.getvalue())
        return out.getvalue(), err.getvalue()

    def test_show_no_file(self, tmp_path):
        out, _ = self._run(["--path", str(tmp_path / "r.json"), "show"])
        assert "no recovery file" in out

    def test_set_and_show(self, tmp_path):
        path = tmp_path / "r.json"
        self._run(["--path", str(path), "set", "--score", "50", "--source", "manual"])
        out, _ = self._run(["--path", str(path), "show"])
        data = json.loads(out.split("\n\n")[0])
        assert data["score"] == 50
        assert data["bucket"] == "yellow"
        assert data["suggest_low_effort_preset"] is False

    def test_set_invalid_score(self, tmp_path):
        _, err = self._run(
            ["--path", str(tmp_path / "r.json"), "set", "--score", "200"],
            expect_status=2,
        )
        assert "0–100" in err

    def test_classify_does_not_write(self, tmp_path):
        path = tmp_path / "r.json"
        out, _ = self._run(["--path", str(path), "classify", "--score", "20"])
        assert "red" in out.splitlines()[0]
        assert not path.exists()

    def test_clear_removes_file(self, tmp_path):
        path = tmp_path / "r.json"
        self._run(["--path", str(path), "set", "--score", "50"])
        assert path.exists()
        out, _ = self._run(["--path", str(path), "clear"])
        assert "deleted" in out
        assert not path.exists()
        # Idempotent.
        out, _ = self._run(["--path", str(path), "clear"])
        assert "no recovery file" in out

    def test_where(self, tmp_path):
        out, _ = self._run(["--path", str(tmp_path / "r.json"), "where"])
        assert str(tmp_path / "r.json") in out

    def test_show_with_bad_file_reports_error(self, tmp_path):
        path = tmp_path / "r.json"
        path.write_text(json.dumps({"score": "abc"}))
        _, err = self._run(["--path", str(path), "show"], expect_status=1)
        assert "score" in err.lower()
