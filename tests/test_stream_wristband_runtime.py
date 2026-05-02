"""Tests for ``stream/wristband_runtime.py``."""

from __future__ import annotations

import asyncio
import sys
import types

import numpy as np
import pytest

import stream.phase3_open_conversation as phase3
from stream.haptic_mapper import HapticMapper
from stream.phase2_training import OUTCOME_CORRECT, Phase2ProgressStore, Phase2TrainingSession
from stream.wristband_runtime import WristbandRuntime, _run_manual


class _StubBleClient:
    def __init__(self):
        self.sent = []

    async def send_packet(self, packet):
        self.sent.append(packet)


class _StopLiveLoop(RuntimeError):
    pass


def test_packet_from_classification(audiogram_path: str):
    runtime = WristbandRuntime(HapticMapper(audiogram_path), _StubBleClient())
    packet = runtime.packet_from_classification("dog", 0.5)
    assert list(packet.to_bytes()) == [4, 64, 4]


def test_send_scores_dispatches_packet_via_ble(audiogram_path: str):
    """``send_scores`` aggregates YAMNet-style scores and forwards over BLE."""
    client = _StubBleClient()
    runtime = WristbandRuntime(HapticMapper(audiogram_path), client)

    packet = asyncio.run(runtime.send_scores({"Doorbell": 0.9, "Music": 0.05}))

    assert client.sent == [packet]
    # Doorbell maps to OpenHear sound class id 2 (see haptic_mapper.SOUND_PROFILES).
    assert packet.to_bytes()[0] == 2


def test_send_scores_silence_when_below_confidence(audiogram_path: str):
    """Low-confidence frames should resolve to the silence packet."""
    client = _StubBleClient()
    runtime = WristbandRuntime(HapticMapper(audiogram_path), client)

    packet = asyncio.run(runtime.send_scores({"Speech": 0.05}))

    # The silence profile's sound_class_id is 0.
    assert packet.to_bytes()[0] == 0
    assert client.sent == [packet]


def test_send_phase2_scores_dispatches_existing_packet_and_logs(audiogram_path: str, tmp_path):
    client = _StubBleClient()
    progress = Phase2ProgressStore(tmp_path / "phase2.json")
    runtime = WristbandRuntime(
        HapticMapper(audiogram_path),
        client,
        phase2_session=Phase2TrainingSession(session_id="s1"),
        phase2_progress=progress,
    )

    packet, event = asyncio.run(runtime.send_phase2_scores("alarm_smoke", {"Smoke detector": 0.9}))

    assert event.outcome == OUTCOME_CORRECT
    assert packet.to_bytes()[0] == 3
    assert client.sent == [packet]
    assert progress.load()["events"][0]["target_id"] == "alarm_smoke"


def test_send_scores_logs_phase3_passive_without_changing_packet(audiogram_path: str, tmp_path):
    client = _StubBleClient()
    progress = phase3.Phase3ProgressStore(tmp_path / "phase3.json")
    runtime = WristbandRuntime(
        HapticMapper(audiogram_path),
        client,
        phase3_session=phase3.Phase3OpenConversationSession(session_id="p3"),
        phase3_progress=progress,
        phase3_environment="home",
        phase3_passive_log=True,
    )

    packet = asyncio.run(runtime.send_scores({"Speech": 0.9}))

    assert client.sent == [packet]
    assert packet.to_bytes()[0] == 1
    stored = progress.load()["passive_events"][0]
    assert stored["predicted_sound_class"] == "voice"
    assert stored["environment_tag"] == "home"


def test_send_phase3_recall_scores_dispatches_existing_packet_and_logs(
    audiogram_path: str, tmp_path
):
    client = _StubBleClient()
    progress = phase3.Phase3ProgressStore(tmp_path / "phase3.json")
    runtime = WristbandRuntime(
        HapticMapper(audiogram_path),
        client,
        phase3_session=phase3.Phase3OpenConversationSession(session_id="p3"),
        phase3_progress=progress,
    )

    packet, event = asyncio.run(
        runtime.send_phase3_recall_scores(
            "classify_voice",
            {"Speech": 0.9},
            user_response="voice",
        )
    )

    assert event.outcome == phase3.OUTCOME_CORRECT
    assert packet.to_bytes()[0] == 1
    assert client.sent == [packet]
    assert progress.load()["recall_events"][0]["prompt_id"] == "classify_voice"


def test_phase2_and_phase3_options_do_not_conflict(audiogram_path: str, tmp_path):
    client = _StubBleClient()
    phase2_progress = Phase2ProgressStore(tmp_path / "phase2.json")
    phase3_progress = phase3.Phase3ProgressStore(tmp_path / "phase3.json")
    runtime = WristbandRuntime(
        HapticMapper(audiogram_path),
        client,
        phase2_session=Phase2TrainingSession(session_id="p2"),
        phase2_progress=phase2_progress,
        phase3_session=phase3.Phase3OpenConversationSession(session_id="p3"),
        phase3_progress=phase3_progress,
        phase3_passive_log=True,
    )

    phase2_packet, phase2_event = asyncio.run(
        runtime.send_phase2_scores("alarm_smoke", {"Smoke detector": 0.9})
    )
    phase3_packet = asyncio.run(runtime.send_scores({"Speech": 0.9}))

    assert phase2_event.outcome == OUTCOME_CORRECT
    assert phase2_packet.to_bytes()[0] == 3
    assert phase3_packet.to_bytes()[0] == 1
    assert phase2_progress.load()["events"][0]["target_id"] == "alarm_smoke"
    assert phase3_progress.load()["passive_events"][0]["predicted_sound_class"] == "voice"


def test_run_manual_prints_packet_for_sound_class(audiogram_path, capsys):
    """The ``--manual-sound`` CLI branch builds a packet without BLE I/O."""
    args = type(
        "Args",
        (),
        {
            "audiogram": audiogram_path,
            "comfort_scale": 1.0,
            "ear_strategy": "worst",
            "sound_class": "alarm",
            "confidence": 1.0,
        },
    )()

    asyncio.run(_run_manual(args))

    out = capsys.readouterr().out.strip()
    # The printed list begins with the alarm sound class id (3).
    assert out.startswith("[3,")


def test_main_requires_model_and_labels_for_live_mode(audiogram_path, monkeypatch):
    """Without ``--manual-sound`` the CLI demands model + labels paths."""
    from stream import wristband_runtime

    monkeypatch.setattr(
        "sys.argv",
        ["wristband_runtime", "--audiogram", audiogram_path],
    )
    with pytest.raises(SystemExit):
        wristband_runtime.main()


def test_main_manual_branch_runs_without_ble(audiogram_path, monkeypatch, capsys):
    from stream import wristband_runtime

    monkeypatch.setattr(
        "sys.argv",
        [
            "wristband_runtime",
            "--audiogram",
            audiogram_path,
            "--manual-sound",
            "doorbell",
        ],
    )
    wristband_runtime.main()
    out = capsys.readouterr().out.strip()
    # Doorbell sound_class_id is 2.
    assert out.startswith("[2,")


def test_main_requires_phase3_progress_for_passive_log(audiogram_path, monkeypatch):
    from stream import wristband_runtime

    monkeypatch.setattr(
        "sys.argv",
        [
            "wristband_runtime",
            "--audiogram",
            audiogram_path,
            "--model",
            "model.tflite",
            "--labels",
            "labels.csv",
            "--phase3-passive-log",
        ],
    )

    with pytest.raises(SystemExit):
        wristband_runtime.main()


def test_run_live_processes_one_frame_and_disconnects(audiogram_path, monkeypatch, capsys):
    from stream import wristband_runtime

    class _FakeInputStream:
        def __init__(self, *, samplerate, channels, dtype, blocksize):
            self.samplerate = samplerate
            self.channels = channels
            self.dtype = dtype
            self.blocksize = blocksize
            self.reads = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, frame_samples):
            assert frame_samples == self.blocksize
            self.reads += 1
            if self.reads > 1:
                raise _StopLiveLoop("stop after one frame")
            return np.zeros((frame_samples, 1), dtype=np.float32), None

    fake_sounddevice = types.SimpleNamespace(InputStream=_FakeInputStream)
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sounddevice)

    class _FakeClassifier:
        def __init__(self, model, labels):
            assert model == "model.tflite"
            assert labels == "labels.csv"

        def classify_window(self, samples, sample_rate):
            assert sample_rate == 16_000
            assert samples.ndim == 1
            return types.SimpleNamespace(
                source_label="Speech",
                sound_key="voice",
                confidence=0.9,
            )

    class _FakeBLEClient(_StubBleClient):
        instances = []

        def __init__(self):
            super().__init__()
            self.connected = False
            self.disconnected = False
            self.__class__.instances.append(self)

        async def connect(self, *, timeout):
            assert timeout == 1.25
            self.connected = True

        async def disconnect(self):
            self.disconnected = True

    monkeypatch.setattr(wristband_runtime, "YamnetClassifier", _FakeClassifier)
    monkeypatch.setattr(wristband_runtime, "OpenHearBLEClient", _FakeBLEClient)
    args = types.SimpleNamespace(
        audiogram=audiogram_path,
        comfort_scale=1.0,
        ear_strategy="worst",
        model="model.tflite",
        labels="labels.csv",
        phase2_target=None,
        phase2_progress=None,
        phase3_passive_log=False,
        phase3_recall_prompt=None,
        phase3_progress=None,
        phase3_environment="",
        phase3_user_response=None,
        phase3_reaction_time_ms=None,
        phase3_user_rating=None,
        scan_timeout=1.25,
    )

    with pytest.raises(_StopLiveLoop):
        asyncio.run(wristband_runtime._run_live(args))

    client = _FakeBLEClient.instances[0]
    assert client.connected is True
    assert client.disconnected is True
    assert client.sent[0].sound_class_id == 1
    assert "voice" in capsys.readouterr().out
