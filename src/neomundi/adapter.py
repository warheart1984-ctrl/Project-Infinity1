"""File/JSONL adapter for NeoMundi measurements."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

from src.neomundi.ingest import ingest_measurement
from src.neomundi.measurement import NeoMundiMeasurement
from src.continuity.cab import CABLedger, EvidenceChain


def default_measurement_dir() -> Path | None:
    override = os.environ.get("NEOMUNDI_MEASUREMENT_DIR", "").strip()
    if not override:
        return None
    return Path(override).expanduser().resolve()


def parse_measurement_record(raw: dict) -> NeoMundiMeasurement:
    return NeoMundiMeasurement(
        measurement_id=str(raw["measurement_id"]),
        signal_type=str(raw.get("signal_type") or "unknown"),
        payload=dict(raw.get("payload") or {}),
        timestamp=str(raw.get("timestamp") or ""),
        integrity=str(raw.get("integrity") or "asserted"),
        source=str(raw.get("source") or "neomundi.local"),
        tags=[str(item) for item in (raw.get("tags") or [])],
    )


def iter_measurements_from_dir(directory: Path) -> Iterator[NeoMundiMeasurement]:
    for path in sorted(directory.glob("**/*")):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                for item in raw:
                    yield parse_measurement_record(dict(item))
            else:
                yield parse_measurement_record(dict(raw))
        elif path.suffix.lower() == ".jsonl":
            for line in path.read_text(encoding="utf-8").splitlines():
                cleaned = line.strip()
                if cleaned:
                    yield parse_measurement_record(json.loads(cleaned))


def ingest_directory(
    directory: Path | None = None,
    *,
    ledger: CABLedger | None = None,
) -> list[EvidenceChain]:
    root = directory or default_measurement_dir()
    if root is None or not root.is_dir():
        return []
    chains: list[EvidenceChain] = []
    for measurement in iter_measurements_from_dir(root):
        chains.append(ingest_measurement(measurement, ledger=ledger))
    return chains
