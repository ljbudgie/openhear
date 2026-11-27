#!/usr/bin/env python3
"""Check the OpenHear Haptics pattern table against the wristband firmware.

Runs every pattern function in wristband/openhear_firmware.py against stub
micro:bit modules, records each sleep() with the motor state at that moment,
and compares the resulting step lists and totals with the table in the app
spec (the same values as OpenHearHaptics/Model/Patterns.swift and the XCTests).

Optionally pass --swift-json FILE: a JSON dump of the Swift table, as printed
by a small Swift program, to compare that too.

Usage, from the repository root:
    python3 ios/OpenHearHaptics/Scripts/check_patterns.py
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FIRMWARE = REPO / "wristband" / "openhear_firmware.py"


def _rep(times, block):
    return [step for _ in range(times) for step in block]


# The table from the app spec. (left, right, ms); (0, 0, ms) is a pause.
SPEC = {
    1: ("voice", _rep(3, [(1, 1, 200), (0, 0, 100)]), 900),
    2: ("doorbell", _rep(2, [(1, 1, 50), (0, 0, 50)]), 200),
    3: (
        "alarm",
        [s for i in range(8) for s in (((1, 0, 30) if i % 2 == 0 else (0, 1, 30)), (0, 0, 30))],
        480,
    ),
    4: ("dog", [(0, 1, 150)], 150),
    5: ("traffic", [(1, 0, 300)], 300),
    6: ("media", _rep(2, [(1, 1, 500), (0, 0, 500)]), 2000),
    7: ("knock", [(1, 1, 80), (0, 0, 40), (1, 1, 40)], 160),
    8: ("baby_cry", _rep(4, [(1, 1, 60), (0, 0, 40)]), 400),
    9: ("phone", _rep(3, [(1, 0, 100), (0, 0, 80), (0, 1, 100), (0, 0, 80)]), 1080),
}


def firmware_steps():
    """Return {pattern_id: [(left, right, ms), ...]} by running the firmware."""
    state = {"p0": 0, "p1": 0}
    steps: list[tuple[int, int, int]] = []

    class Pin:
        def __init__(self, key):
            self.key = key

        def write_analog(self, value):
            state[self.key] = value

    def sleep(ms):
        if ms > 0:
            steps.append((1 if state["p0"] else 0, 1 if state["p1"] else 0, int(ms)))

    microbit = types.ModuleType("microbit")
    microbit.pin0, microbit.pin1 = Pin("p0"), Pin("p1")
    microbit.sleep = sleep
    microbit.display = types.SimpleNamespace(show=lambda *_: None)
    bluetooth = types.ModuleType("bluetooth")
    bluetooth.UARTService = object
    sys.modules["microbit"] = microbit
    sys.modules["bluetooth"] = bluetooth

    tree = ast.parse(FIRMWARE.read_text(encoding="utf-8"))
    # Drop the trailing main() call so the module can be loaded.
    tree.body = [
        node
        for node in tree.body
        if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "id", None) == "main")
    ]
    namespace: dict = {}
    exec(compile(tree, str(FIRMWARE), "exec"), namespace)

    result = {}
    for pattern_id, handler in namespace["PATTERNS"].items():
        if pattern_id == 0:
            continue
        steps.clear()
        state.update(p0=0, p1=0)
        handler(200)
        result[pattern_id] = list(steps)
    return result, namespace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--swift-json", type=Path)
    args = parser.parse_args()

    ok = True
    fw, namespace = firmware_steps()
    if sorted(fw) != list(range(1, 10)):
        print(f"FAIL firmware pattern ids are {sorted(fw)}, expected 1-9")
        ok = False

    for pattern_id, (key, spec_steps, spec_total) in SPEC.items():
        got = fw.get(pattern_id, [])
        total = sum(ms for _, _, ms in got)
        handler_name = namespace["PATTERNS"][pattern_id].__name__
        if handler_name != f"_pattern_{key}":
            print(f"FAIL id {pattern_id}: firmware handler is {handler_name}, expected _pattern_{key}")
            ok = False
        if got != spec_steps:
            print(f"FAIL id {pattern_id} {key}: firmware steps {got} != spec {spec_steps}")
            ok = False
        if total != spec_total or sum(ms for *_, ms in spec_steps) != spec_total:
            print(f"FAIL id {pattern_id} {key}: firmware total {total} ms, spec total {spec_total} ms")
            ok = False
        else:
            print(f"ok   id {pattern_id} {key:9s} {len(got):2d} steps, {total:4d} ms")

    if args.swift_json:
        swift = {item["id"]: item for item in json.loads(args.swift_json.read_text())}
        for pattern_id, (key, spec_steps, spec_total) in SPEC.items():
            item = swift.get(pattern_id)
            if (item is None or item["key"] != key or item["total"] != spec_total
                    or [tuple(s) for s in item["steps"]] != spec_steps):
                print(f"FAIL id {pattern_id} {key}: Swift table differs: {item}")
                ok = False
        if ok:
            print("ok   Swift table matches firmware and spec for all nine patterns")

    print("ALL MATCH" if ok else "MISMATCH FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
