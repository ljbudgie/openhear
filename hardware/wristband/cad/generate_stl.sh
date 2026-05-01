#!/usr/bin/env bash
set -euo pipefail
SCAD_FILE="${1:-parametric_wristband_v1.scad}"
OUT_DIR="${2:-stl}"
mkdir -p "$OUT_DIR"
openscad -o "$OUT_DIR/openhear-wristband-v1-24actuator-160mm.stl" -D wrist_circumference_mm=160 -D actuator_count=24 -D mic_count=8 "$SCAD_FILE"
openscad -o "$OUT_DIR/openhear-wristband-v1-64actuator-180mm.stl" -D wrist_circumference_mm=180 -D actuator_count=64 -D mic_count=8 "$SCAD_FILE"
openscad -o "$OUT_DIR/openhear-wristband-v1-128actuator-200mm.stl" -D wrist_circumference_mm=200 -D actuator_count=128 -D mic_count=16 "$SCAD_FILE"
