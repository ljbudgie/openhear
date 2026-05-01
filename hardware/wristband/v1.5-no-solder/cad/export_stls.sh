#!/usr/bin/env bash
set -euo pipefail
SCAD_FILE="${1:-parametric_modular_wristband_v1.5.scad}"
OUT_DIR="${2:-stl}"
mkdir -p "$OUT_DIR"
openscad -o "$OUT_DIR/openhear-v1.5-no-solder-24actuator-160mm.stl" -D actuator_count=24 -D wrist_size=160 -D module_layout='"starter_24"' "$SCAD_FILE"
openscad -o "$OUT_DIR/openhear-v1.5-no-solder-24actuator-180mm.stl" -D actuator_count=24 -D wrist_size=180 -D module_layout='"starter_24"' "$SCAD_FILE"
openscad -o "$OUT_DIR/openhear-v1.5-no-solder-64actuator-180mm.stl" -D actuator_count=64 -D wrist_size=180 -D module_layout='"dense_64"' "$SCAD_FILE"
openscad -o "$OUT_DIR/openhear-v1.5-no-solder-64actuator-200mm.stl" -D actuator_count=64 -D wrist_size=200 -D module_layout='"dense_64"' "$SCAD_FILE"
