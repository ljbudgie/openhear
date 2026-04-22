You are building OpenHear: an open-source sovereign audio pipeline and aids-free haptic wristband for hearing users.

Core rules:
- Prioritize data sovereignty: no cloud, on-device only, user-owned JSON/Parquet, user-signed firmware.
- All AI/ML must be edge/on-device (YAMNet, TFLite, PyTorch mobile, etc.). No proprietary models.
- Target ≤5ms latency where possible.
- Follow the 8-9 pillars from README: peak hearing, selective sovereignty, therapeutic haptics, etc.
- Always add tests, update docs/CHANGELOG, keep code modular and inspectable.
- Hardware path: start with micro:bit prototype → Raspberry Pi CM4 → RISC-V/FPGA → custom NPU.
- Use existing structure: enhance dsp/, wristband/, learn/, voice/, mobile/, etc.

Tech preferences: Python for pipeline, Kotlin for Android, C++ for performance-critical, OpenSCAD for hardware.
