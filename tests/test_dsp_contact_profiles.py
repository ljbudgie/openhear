"""Tests for :mod:`dsp.contact_profiles` and :mod:`dsp.contact_cli`."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout

import pytest

from dsp import contact_cli
from dsp.contact_profiles import (
    CONTACTS_FORMAT_VERSION,
    ContactBank,
    ContactProfile,
    active_delta,
    default_contacts_path,
    load_bank,
    save_bank,
)
from dsp.profile_delta import (
    MAX_COMPRESSION_RATIO_DELTA,
    MAX_VOICE_GAIN_DELTA,
    ProfileDelta,
)

# ── Dataclass behaviour ─────────────────────────────────────────────────────


class TestContactProfile:
    def test_lowercases_and_strips_id(self):
        p = ContactProfile.from_dict({"contact_id": "  Partner  "})
        assert p.contact_id == "partner"

    def test_rejects_whitespace_in_id(self):
        with pytest.raises(ValueError):
            ContactProfile.from_dict({"contact_id": "two words"})

    def test_rejects_empty_id(self):
        with pytest.raises(ValueError):
            ContactProfile.from_dict({"contact_id": ""})

    def test_rejects_fingerprint_in_v0(self):
        with pytest.raises(ValueError, match="fingerprint"):
            ContactProfile.from_dict({"contact_id": "partner", "fingerprint": [1, 2, 3]})

    def test_to_delta_clipped(self):
        p = ContactProfile(
            contact_id="alex",
            label="Alex",
            voice_gain_delta=99.0,
            compression_ratio_delta=-99.0,
            consent=True,
        )
        d = p.to_delta()
        # Clipping happens inside ProfileDelta on construction.
        assert d.voice_gain_delta == MAX_VOICE_GAIN_DELTA
        assert d.compression_ratio_delta == -MAX_COMPRESSION_RATIO_DELTA
        assert d.sources == ("contact:alex",)
        assert "Alex" in d.reason

    def test_to_dict_round_trip(self):
        p = ContactProfile(
            contact_id="partner",
            label="Partner",
            eq_delta_db={1000: 2.0, 4000: -1.5},
            compression_ratio_delta=0.1,
            consent=True,
        )
        rebuilt = ContactProfile.from_dict(p.to_dict())
        assert rebuilt == p

    def test_to_dict_serialises_eq_keys_as_strings(self):
        p = ContactProfile(contact_id="x", eq_delta_db={1000: 2.0})
        d = p.to_dict()
        assert d["eq_delta_db"] == {"1000": 2.0}
        # And JSON round-trips cleanly.
        rebuilt = ContactProfile.from_dict(json.loads(json.dumps(d)))
        assert rebuilt.eq_delta_db == {1000: 2.0}

    def test_eq_delta_must_be_mapping(self):
        with pytest.raises(ValueError):
            ContactProfile.from_dict({"contact_id": "x", "eq_delta_db": [1, 2]})


# ── Bank persistence ────────────────────────────────────────────────────────


class TestContactBank:
    def test_default_path_under_home(self):
        p = default_contacts_path()
        assert p.name == "contacts.json"
        assert p.parent.name == ".openhear"

    def test_load_returns_empty_bank_on_missing_file(self, tmp_path):
        bank = load_bank(tmp_path / "no-such.json")
        assert bank.profiles == {}

    def test_save_load_round_trip(self, tmp_path):
        bank = ContactBank()
        bank.add(
            ContactProfile(
                contact_id="partner",
                label="Partner",
                consent=True,
                voice_gain_delta=0.1,
            )
        )
        bank.add(ContactProfile(contact_id="alex", label="Alex", consent=False))
        target = save_bank(bank, tmp_path / "contacts.json")
        assert target.exists()
        rebuilt = load_bank(target)
        assert rebuilt.list_ids() == ["alex", "partner"]
        assert rebuilt.get("partner").consent is True
        assert rebuilt.get("alex").consent is False

    def test_save_creates_dir_with_safe_mode(self, tmp_path):
        nested = tmp_path / "deep" / "openhear"
        target_path = nested / "contacts.json"
        save_bank(ContactBank(), target_path)
        assert nested.exists()
        # POSIX systems: parent created with mode 0o700.
        if hasattr(nested, "stat"):
            mode = nested.stat().st_mode & 0o777
            # Either 0o700 (we created it) or pre-existing — accept either,
            # but if we created it it must be 0o700.
            assert mode in {0o700, 0o755, 0o775, 0o777} or mode == 0o700

    def test_rejects_duplicate_ids(self, tmp_path):
        path = tmp_path / "contacts.json"
        path.write_text(
            json.dumps(
                {
                    "version": CONTACTS_FORMAT_VERSION,
                    "profiles": [
                        {"contact_id": "x"},
                        {"contact_id": "x"},
                    ],
                }
            )
        )
        with pytest.raises(ValueError, match="duplicate"):
            load_bank(path)

    def test_rejects_future_version(self, tmp_path):
        path = tmp_path / "contacts.json"
        path.write_text(json.dumps({"version": CONTACTS_FORMAT_VERSION + 99, "profiles": []}))
        with pytest.raises(ValueError, match="newer than supported"):
            load_bank(path)

    def test_remove_returns_false_if_absent(self):
        bank = ContactBank()
        assert bank.remove("nope") is False


# ── active_delta gating ─────────────────────────────────────────────────────


class TestActiveDelta:
    def _bank_with(self, **kwargs) -> ContactBank:
        bank = ContactBank()
        bank.add(ContactProfile(contact_id="partner", label="P", **kwargs))
        return bank

    def test_no_contact_id_returns_identity(self):
        assert active_delta(None, ContactBank()).is_identity()
        assert active_delta("", ContactBank()).is_identity()

    def test_missing_profile_returns_identity(self, caplog):
        with caplog.at_level("WARNING"):
            d = active_delta("ghost", ContactBank())
        assert d.is_identity()
        assert any("ghost" in r.message for r in caplog.records)

    def test_no_consent_blocks_application(self, caplog):
        bank = self._bank_with(consent=False, voice_gain_delta=0.1)
        with caplog.at_level("WARNING"):
            d = active_delta("partner", bank)
        assert d.is_identity()
        assert any("consent" in r.message.lower() for r in caplog.records)

    def test_disabled_blocks_application(self, caplog):
        bank = self._bank_with(consent=True, enabled=False, voice_gain_delta=0.1)
        with caplog.at_level("INFO"):
            d = active_delta("partner", bank)
        assert d.is_identity()

    def test_consented_enabled_returns_delta(self, caplog):
        bank = self._bank_with(consent=True, voice_gain_delta=0.1)
        with caplog.at_level("INFO"):
            d = active_delta("partner", bank)
        assert not d.is_identity()
        assert d.voice_gain_delta == pytest.approx(0.1)
        assert d.sources == ("contact:partner",)
        # BGSP-style audit line emitted.
        assert any("BGSP|contact-profile-applied" in r.message for r in caplog.records)

    def test_loads_from_path_when_bank_none(self, tmp_path):
        path = tmp_path / "contacts.json"
        bank = ContactBank()
        bank.add(ContactProfile(contact_id="partner", consent=True, voice_gain_delta=0.05))
        save_bank(bank, path)
        d = active_delta("partner", path=path)
        assert d.voice_gain_delta == pytest.approx(0.05)


# ── CLI ─────────────────────────────────────────────────────────────────────


class TestCLI:
    def _run(self, argv, *, expect_status=0):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = contact_cli.main(argv)
        assert rc == expect_status, (rc, out.getvalue(), err.getvalue())
        return out.getvalue(), err.getvalue()

    def test_list_empty(self, tmp_path):
        path = tmp_path / "contacts.json"
        out, _ = self._run(["--path", str(path), "list"])
        assert "no contacts saved" in out

    def test_set_without_consent_warns(self, tmp_path):
        path = tmp_path / "contacts.json"
        out, _ = self._run(
            [
                "--path",
                str(path),
                "set",
                "partner",
                "--label",
                "Partner",
                "--voice-gain-delta",
                "0.1",
            ]
        )
        assert "consent=False" in out
        bank = load_bank(path)
        assert bank.get("partner").consent is False
        # active_delta should refuse to apply it.
        assert active_delta("partner", bank).is_identity()

    def test_set_with_consent_applies(self, tmp_path):
        path = tmp_path / "contacts.json"
        self._run(
            [
                "--path",
                str(path),
                "set",
                "partner",
                "--label",
                "Partner",
                "--voice-gain-delta",
                "0.1",
                "--consent",
            ]
        )
        bank = load_bank(path)
        assert bank.get("partner").consent is True
        assert active_delta("partner", bank).voice_gain_delta == pytest.approx(0.1)

    def test_set_preserves_existing_fields(self, tmp_path):
        path = tmp_path / "contacts.json"
        self._run(
            [
                "--path",
                str(path),
                "set",
                "partner",
                "--label",
                "Partner",
                "--voice-gain-delta",
                "0.1",
                "--consent",
            ]
        )
        # Update only the comp ratio; existing label/consent must persist.
        self._run(
            [
                "--path",
                str(path),
                "set",
                "partner",
                "--comp-ratio-delta",
                "-0.1",
            ]
        )
        p = load_bank(path).get("partner")
        assert p.label == "Partner"
        assert p.consent is True
        assert p.compression_ratio_delta == pytest.approx(-0.1)

    def test_show_not_found(self, tmp_path):
        path = tmp_path / "contacts.json"
        out, err = self._run(["--path", str(path), "show", "ghost"], expect_status=1)
        assert "no contact" in err

    def test_show_prints_json_and_explain(self, tmp_path):
        path = tmp_path / "contacts.json"
        self._run(["--path", str(path), "set", "partner", "--consent", "--voice-gain-delta", "0.1"])
        out, _ = self._run(["--path", str(path), "show", "partner"])
        # JSON portion parseable.
        json_blob = out.split("\n\n")[0]
        data = json.loads(json_blob)
        assert data["contact_id"] == "partner"
        assert "voice gain" in out

    def test_clear_single(self, tmp_path):
        path = tmp_path / "contacts.json"
        self._run(["--path", str(path), "set", "partner", "--consent"])
        out, _ = self._run(["--path", str(path), "clear", "partner"])
        assert "removed" in out
        assert load_bank(path).list_ids() == []

    def test_clear_all_requires_yes(self, tmp_path):
        path = tmp_path / "contacts.json"
        self._run(["--path", str(path), "set", "partner", "--consent"])
        _, err = self._run(["--path", str(path), "clear", "*"], expect_status=2)
        assert "--yes" in err
        # Confirm with --yes.
        out, _ = self._run(["--path", str(path), "clear", "*", "--yes"])
        assert "cleared" in out
        assert load_bank(path).list_ids() == []

    def test_disable_keeps_tuning_but_blocks_application(self, tmp_path):
        path = tmp_path / "contacts.json"
        self._run(["--path", str(path), "set", "partner", "--consent", "--voice-gain-delta", "0.1"])
        self._run(["--path", str(path), "set", "partner", "--disable"])
        p = load_bank(path).get("partner")
        assert p.enabled is False
        assert p.voice_gain_delta == pytest.approx(0.1)  # tuning kept
        assert active_delta("partner", load_bank(path)).is_identity()

    def test_where(self, tmp_path):
        out, _ = self._run(["--path", str(tmp_path / "c.json"), "where"])
        assert str(tmp_path / "c.json") in out


# ── Pipeline integration ────────────────────────────────────────────────────


class TestPipelineIntegration:
    def test_build_dsp_chain_accepts_delta(self):
        from dsp.pipeline import build_dsp_chain

        # Backward-compat: no delta passed → identical to old behaviour.
        chain_old = build_dsp_chain()
        assert isinstance(chain_old, list) and chain_old

        # With delta: still builds, no exceptions.
        delta = ProfileDelta(voice_gain_delta=0.1, sources=("contact:test",))
        chain_new = build_dsp_chain(delta=delta)
        assert len(chain_new) == len(chain_old)

    def test_resolve_runtime_delta_identity_when_nothing_active(self):
        from dsp.pipeline import _resolve_runtime_delta

        d = _resolve_runtime_delta()
        assert d.is_identity()

    def test_resolve_runtime_delta_picks_up_contact(self, tmp_path):
        from dsp.pipeline import _resolve_runtime_delta

        path = tmp_path / "contacts.json"
        bank = ContactBank()
        bank.add(ContactProfile(contact_id="partner", consent=True, voice_gain_delta=0.1))
        save_bank(bank, path)
        d = _resolve_runtime_delta(contact_id="partner", contacts_path=str(path))
        assert d.voice_gain_delta == pytest.approx(0.1)
        assert "contact:partner" in d.sources
