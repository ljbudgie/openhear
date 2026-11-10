"""Tests for scripts/bench_datasets.py metadata handling (no audio)."""

import io
import zipfile

import numpy as np
import pytest

from scripts import bench_datasets as datasets


def test_esc50_engine_is_target_under_old_scheme_and_negative_under_new():
    rows = [
        {"filename": "b.wav", "category": "engine"},
        {"filename": "a.wav", "category": "car_horn"},
        {"filename": "c.wav", "category": "rain"},
    ]
    specs = {spec.clip_id: spec for spec in datasets.esc50_specs(rows)}
    assert list(specs) == ["a.wav", "b.wav", "c.wav"]
    engine = specs["b.wav"]
    assert engine.targets["v1.7.0"] == {"traffic"} and not engine.negative["v1.7.0"]
    assert engine.targets["v1.8.0"] == frozenset() and engine.negative["v1.8.0"]
    assert specs["a.wav"].targets["v1.8.0"] == {"traffic"}
    assert specs["c.wav"].negative == {"v1.7.0": True, "v1.8.0": True}
    assert engine.path == "audio/b.wav" and engine.groups == ("engine",)


@pytest.mark.parametrize(
    ("url", "allowed"),
    [
        ("http://creativecommons.org/publicdomain/zero/1.0/", True),
        ("http://creativecommons.org/licenses/by/3.0/", True),
        ("https://creativecommons.org/licenses/by/4.0/", True),
        ("http://creativecommons.org/licenses/by-nc/3.0/", False),
        ("http://creativecommons.org/licenses/by-nc/4.0/", False),
        ("http://creativecommons.org/licenses/sampling+/1.0/", False),
        ("", False),
        ("something else", False),
    ],
)
def test_fsd50k_licence_filter(url, allowed):
    assert datasets.fsd50k_licence_allowed(url) is allowed


def test_fsd50k_specs_filter_licences_and_map_labels():
    rows = [
        {"fname": "30", "labels": "Doorbell,Alarm"},
        {"fname": "20", "labels": "Car,Vehicle,Motor_vehicle_(road)"},
        {"fname": "10", "labels": "Knock"},
        {"fname": "40", "labels": "Rain,Water"},
        {"fname": "50", "labels": "Ringtone,Telephone"},
    ]
    info = {
        "10": {"license": "http://creativecommons.org/licenses/by-nc/3.0/"},
        "20": {"license": "http://creativecommons.org/licenses/by/3.0/"},
        "30": {"license": "http://creativecommons.org/publicdomain/zero/1.0/"},
        "40": {"license": "http://creativecommons.org/publicdomain/zero/1.0/"},
        "50": {"license": "http://creativecommons.org/licenses/sampling+/1.0/"},
    }
    vocabulary = {"Doorbell", "Alarm", "Car", "Knock", "Ringtone", "Telephone", "Rain"}
    specs, notes = datasets.fsd50k_specs(rows, info, vocabulary)
    by_id = {spec.clip_id: spec for spec in specs}
    assert list(by_id) == ["20", "30", "40"]
    assert by_id["30"].targets["v1.8.0"] == {"doorbell", "alarm"}
    assert by_id["20"].targets["v1.7.0"] == {"traffic"}
    assert by_id["20"].targets["v1.8.0"] == frozenset() and by_id["20"].negative["v1.8.0"]
    assert by_id["40"].negative == {"v1.7.0": True, "v1.8.0": True}
    assert by_id["30"].path == "30.wav"
    assert notes["clips_kept"] == 3
    assert sum(notes["clips_dropped_by_licence"].values()) == 2
    assert "Doorbell" in notes["labels_found_in_vocabulary"]
    assert "Speech" in notes["labels_not_in_vocabulary"]


_SONYC_FIELDS = [
    "split",
    "audio_filename",
    "annotator_id",
    "1-1_small-sounding-engine_presence",
    "5-1_car-horn_presence",
    "5-2_car-alarm_presence",
    "5-3_siren_presence",
    "5-4_reverse-beeper_presence",
    "1_engine_presence",
    "5_alert-signal_presence",
    "6_music_presence",
    "7_human-voice_presence",
    "8_dog_presence",
]


def _sonyc_row(name, annotator="0", **present):
    row = dict.fromkeys(_SONYC_FIELDS, "0")
    row.update({"split": "test", "audio_filename": name, "annotator_id": annotator})
    for column in _SONYC_FIELDS:
        for key in present:
            if column.partition("_")[2] == f"{key}_presence":
                row[column] = "1"
    return row


def test_sonyc_specs_use_verified_rows_and_separate_horns_from_engines():
    rows = [
        _sonyc_row("horn.wav", **{"car-horn": 1, "alert-signal": 1, "engine": 1}),
        _sonyc_row("siren.wav", **{"siren": 1, "alert-signal": 1}),
        _sonyc_row("engine.wav", **{"engine": 1}),
        _sonyc_row("engine_voice.wav", **{"engine": 1, "human-voice": 1}),
        _sonyc_row("quiet.wav"),
        _sonyc_row("crowd.wav", annotator="57", **{"car-horn": 1}),
        _sonyc_row("horn.wav", **{"car-horn": 1}),  # duplicate filename ignored
    ]
    specs, notes = datasets.sonyc_specs(rows, _SONYC_FIELDS)
    by_id = {spec.clip_id: spec for spec in specs}
    assert sorted(by_id) == ["engine.wav", "horn.wav", "siren.wav"]
    assert by_id["horn.wav"].targets["v1.8.0"] == {"traffic"}
    assert not by_id["horn.wav"].negative["v1.8.0"]
    assert by_id["siren.wav"].targets["v1.8.0"] == {"alarm"}
    engine = by_id["engine.wav"]
    assert engine.labels == ("engine_only",)
    assert engine.targets["v1.7.0"] == {"traffic"} and not engine.negative["v1.7.0"]
    assert engine.targets["v1.8.0"] == frozenset() and engine.negative["v1.8.0"]
    assert notes["verified_recordings"] == 5
    assert notes["clips_left_out_no_usable_tag"] == 2
    assert notes["columns_missing"] == []
    assert notes["columns_used"]["engine"] == "1_engine_presence"
    assert notes["columns_used"]["car_horn"] == "5-1_car-horn_presence"


def test_sonyc_reports_missing_columns_instead_of_guessing():
    fields = ["split", "audio_filename", "annotator_id", "5-1_car-horn_presence"]
    specs, notes = datasets.sonyc_specs([], fields)
    assert specs == []
    assert "siren" in notes["columns_missing"] and "engine" in notes["columns_missing"]


def test_iter_audio_reads_from_zip_and_skips_missing(tmp_path):
    sf = pytest.importorskip("soundfile")
    buffer = io.BytesIO()
    sf.write(buffer, np.zeros(1600, dtype=np.float32), 16_000, format="WAV")
    archive = tmp_path / "audio.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("FSD50K.eval_audio/30.wav", buffer.getvalue())
    specs = [
        datasets.ClipSpec("30", "30.wav", ("Doorbell",)),
        datasets.ClipSpec("31", "31.wav", ("Knock",)),
    ]
    found = list(datasets.iter_audio(specs, audio_zip=archive))
    assert [spec.clip_id for spec, _, _ in found] == ["30"]
    assert found[0][2] == 16_000 and len(found[0][1]) == 1600
