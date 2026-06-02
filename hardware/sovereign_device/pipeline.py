"""
pipeline.py – Phase 5 sovereign-device bundle generation.

The Phase 5 software deliverable is intentionally local-only: it turns an
OpenHear audiogram into firmware plus a verifiable build manifest, validates a
community component database, and records cost/safety/sovereignty checks without
uploading audiograms, firmware, or telemetry anywhere.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hardware.tympan.audiogram_to_tympan import generate_binaural_sketch, generate_tympan_sketch

COMPONENT_DATABASE_SCHEMA = "openhear-phase5-component-db-v1"
MANIFEST_SCHEMA = "openhear-phase5-device-build-v1"
DEFAULT_COST_TARGET_GBP = 100.0
_DEFAULT_COMPONENT_DB = Path(__file__).with_name("components.json")
_REQUIRED_ROLES = {
    "shell",
    "receiver",
    "microphone",
    "processor",
    "power",
    "safety_limiter",
    "programming",
}

@dataclass(frozen=True)
class Component:
    """One community-maintained commodity/open component entry."""

    component_id: str
    role: str
    part: str
    category: str
    unit_cost_gbp: float
    quantity: int
    proprietary: bool
    firmware_license: str
    supplier_count: int
    verified_supplier_regions: tuple[str, ...]
    notes: str = ""

    @property
    def extended_cost_gbp(self) -> float:
        """Return the quantity-adjusted cost contribution."""
        return round(self.unit_cost_gbp * self.quantity, 2)

    @property
    def is_sovereign(self) -> bool:
        """Return true if the component has no proprietary firmware dependency."""
        return not self.proprietary and self.firmware_license.lower() != "proprietary"

@dataclass(frozen=True)
class Phase5BuildManifest:
    """Verifiable output manifest for one generated Phase 5 device bundle."""

    schema_version: str
    generated_at: str
    mode: str
    ear: str | None
    audiogram_sha256: str
    firmware_file: str
    firmware_sha256: str
    component_database_version: str
    component_database_sha256: str
    component_cost_gbp: float
    cost_target_gbp: float
    cost_target_met: bool
    components: list[dict[str, Any]]
    safety_requirements: list[str]
    sovereignty_guarantees: list[str]
    regulatory_status: str


def load_component_database(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate a Phase 5 component database document."""
    db_path = Path(path) if path is not None else _DEFAULT_COMPONENT_DB
    data = json.loads(db_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != COMPONENT_DATABASE_SCHEMA:
        raise ValueError(f"Unsupported component database schema: {data.get('schema_version')!r}")
    if data.get("currency") != "GBP":
        raise ValueError("Phase 5 component database must use GBP costs.")
    components = data.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("Phase 5 component database must contain components.")
    parsed = [_component_from_mapping(raw) for raw in components]
    missing = _REQUIRED_ROLES - {component.role for component in parsed}
    if missing:
        raise ValueError(
            f"Phase 5 component database is missing roles: {', '.join(sorted(missing))}"
        )
    for component in parsed:
        if not component.is_sovereign:
            raise ValueError(f"Component {component.component_id!r} is proprietary.")
        if component.supplier_count == 0:
            raise ValueError(f"Component {component.component_id!r} has no verified suppliers.")
    return data


def list_components(path: str | Path | None = None) -> list[Component]:
    """Return validated component entries in database order."""
    data = load_component_database(path)
    raw_components = data["components"]
    assert isinstance(raw_components, list)
    return [_component_from_mapping(raw) for raw in raw_components]


def estimate_binaural_cost(path: str | Path | None = None) -> float:
    """Return the total cost estimate for one binaural Phase 5 build."""
    return round(sum(component.extended_cost_gbp for component in list_components(path)), 2)


def generate_phase5_device_bundle(
    audiogram_path: str | Path,
    output_dir: str | Path,
    *,
    ear: str = "right",
    binaural: bool = True,
    component_db_path: str | Path | None = None,
    cost_target_gbp: float = DEFAULT_COST_TARGET_GBP,
) -> Phase5BuildManifest:
    """Generate firmware and a manifest for an offline Phase 5 device bundle."""
    if ear not in {"right", "left"}:
        raise ValueError("ear must be 'right' or 'left'.")
    component_db = load_component_database(component_db_path)
    component_db_file = (
        Path(component_db_path) if component_db_path is not None else _DEFAULT_COMPONENT_DB
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    mode = "binaural" if binaural else "single-ear"
    firmware_name = "openhear_phase5_binaural.ino" if binaural else f"openhear_phase5_{ear}.ino"
    firmware_path = output / firmware_name
    if binaural:
        generate_binaural_sketch(str(audiogram_path), str(firmware_path))
    else:
        generate_tympan_sketch(str(audiogram_path), str(firmware_path), ear=ear)

    cost = estimate_binaural_cost(component_db_file)
    manifest = Phase5BuildManifest(
        schema_version=MANIFEST_SCHEMA,
        generated_at=datetime.now(timezone.utc).isoformat(),
        mode=mode,
        ear=None if binaural else ear,
        audiogram_sha256=_sha256_file(Path(audiogram_path)),
        firmware_file=firmware_path.name,
        firmware_sha256=_sha256_file(firmware_path),
        component_database_version=str(component_db.get("version", "")),
        component_database_sha256=_sha256_file(component_db_file),
        component_cost_gbp=cost,
        cost_target_gbp=float(cost_target_gbp),
        cost_target_met=cost <= cost_target_gbp,
        components=[
            _manifest_component(component) for component in list_components(component_db_file)
        ],
        safety_requirements=[
            "Passive hardware MPO limiter is mandatory and cannot be bypassed by firmware.",
            "Generated firmware must be calibrated on real hardware before use.",
            "OpenHear remains experimental and is not a certified medical device.",
        ],
        sovereignty_guarantees=[
            "Audiogram processing runs locally.",
            "Manifest stores hashes, not audiogram thresholds or raw audio.",
            "No proprietary component or firmware dependency is allowed in the component database.",
            "No cloud service is required to generate, inspect, or flash the bundle.",
        ],
        regulatory_status=(
            "Research/DIY PSAP scaffold only; CE/FDA/UK MDR classification is not claimed."
        ),
    )
    (output / "manifest.json").write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _component_from_mapping(raw: object) -> Component:
    if not isinstance(raw, dict):
        raise ValueError("Each component entry must be a JSON object.")
    suppliers = raw.get("suppliers")
    if not isinstance(suppliers, list):
        raise ValueError(f"Component {raw.get('id')!r} must contain a suppliers list.")
    verified_regions = tuple(
        str(supplier.get("region", ""))
        for supplier in suppliers
        if isinstance(supplier, dict) and supplier.get("verified") is True
    )
    return Component(
        component_id=str(raw["id"]),
        role=str(raw["role"]),
        part=str(raw["part"]),
        category=str(raw["category"]),
        unit_cost_gbp=float(raw["unit_cost_gbp"]),
        quantity=int(raw.get("quantity", 1)),
        proprietary=bool(raw.get("proprietary", False)),
        firmware_license=str(raw.get("firmware_license", "none")),
        supplier_count=len(verified_regions),
        verified_supplier_regions=verified_regions,
        notes=str(raw.get("notes", "")),
    )


def _manifest_component(component: Component) -> dict[str, Any]:
    return {
        "id": component.component_id,
        "role": component.role,
        "part": component.part,
        "category": component.category,
        "unit_cost_gbp": component.unit_cost_gbp,
        "quantity": component.quantity,
        "extended_cost_gbp": component.extended_cost_gbp,
        "supplier_count": component.supplier_count,
        "verified_supplier_regions": list(component.verified_supplier_regions),
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    """Command-line entry point for Phase 5 bundle generation."""
    parser = argparse.ArgumentParser(
        description="Generate an offline OpenHear Phase 5 firmware bundle and manifest.",
        epilog="Your audiogram, your firmware, your device — no cloud required.",
    )
    parser.add_argument("audiogram", help="Path to an openhear-audiogram-v1 JSON file.")
    parser.add_argument("output_dir", help="Directory for firmware and manifest.json.")
    parser.add_argument("--ear", choices=["right", "left"], default="right")
    parser.add_argument(
        "--single-ear", action="store_true", help="Generate for one ear instead of binaural."
    )
    parser.add_argument("--component-db", help="Override the Phase 5 component database JSON.")
    parser.add_argument("--cost-target", type=float, default=DEFAULT_COST_TARGET_GBP)
    args = parser.parse_args()

    manifest = generate_phase5_device_bundle(
        args.audiogram,
        args.output_dir,
        ear=args.ear,
        binaural=not args.single_ear,
        component_db_path=args.component_db,
        cost_target_gbp=args.cost_target,
    )
    print(f"Phase 5 bundle written to {Path(args.output_dir).resolve()}")
    print(f"Estimated binaural component cost: £{manifest.component_cost_gbp:.2f}")
    print(f"Cost target met: {manifest.cost_target_met}")


if __name__ == "__main__":
    main()
